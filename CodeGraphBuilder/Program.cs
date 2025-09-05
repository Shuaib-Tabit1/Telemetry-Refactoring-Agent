using System.CommandLine;
using System.CommandLine.Invocation;
using System.CommandLine.Binding;
using System.Text.Json;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using Microsoft.CodeAnalysis.MSBuild;

// ------------------------------------------------------------------
// DEFINE THE DATA MODEL FOR OUR GRAPH
// ------------------------------------------------------------------

public enum SymbolKind { Class, Interface, Method }
public enum RelationshipKind { InheritsFrom, Implements, Calls }

/// <summary>
/// Represents a relationship between two code symbols.
/// </summary>
public record SymbolRelationship(string TargetSymbolFullName, RelationshipKind Kind);

/// <summary>
/// Represents a single symbol (class, method, etc.) found in the codebase.
/// </summary>
public record CodeSymbol(
    string FullName,
    SymbolKind Kind,
    string FilePath,
    int LineNumber,
    List<SymbolRelationship> Relationships
);

/// <summary>
/// The top-level object that holds the entire code graph.
/// </summary>
public record CodeGraph(List<CodeSymbol> Symbols);


// ------------------------------------------------------------------
// SET UP THE APPLICATION'S COMMAND-LINE INTERFACE
// ------------------------------------------------------------------

class Program
{
    static async Task<int> Main(string[] args)
    {
        // Option for the index command
        var projectsFileOption = new Option<FileInfo>(
            name: "--projects-file",
            description: "A text file containing the full paths to .csproj files, one per line.")
            { IsRequired = true };

        var outputFileOption = new Option<FileInfo>(
            name: "--output-file",
            description: "The path to save the output graph JSON file.",
            getDefaultValue: () => new FileInfo("codegraph.json"));
        
        // Options for the query command
        var graphFileOption = new Option<FileInfo>(
            name: "--graph-file",
            description: "Path to the pre-built codegraph.json file.")
            { IsRequired = true };

        var seedFilesOption = new Option<string[]>(
            name: "--seed-files",
            description: "A list of seed file paths to start the graph traversal from.")
            { IsRequired = true, Arity = ArgumentArity.OneOrMore };

        // Define the 'index' and 'query' commands
        var indexCommand = new Command("index", "Builds a unified code graph from a list of projects in a file.")
        {
            projectsFileOption,
            outputFileOption
        };
        var queryCommand = new Command("query", "Queries the code graph to find related files.")
        {
            graphFileOption,
            seedFilesOption
        };

        var rootCommand = new RootCommand("C# Code Graph Builder");
        rootCommand.AddCommand(indexCommand);
        rootCommand.AddCommand(queryCommand);

        indexCommand.SetHandler(async (projectsFile, outputFile) =>
        {
            await BuildGraph(projectsFile.FullName, outputFile.FullName);
        }, projectsFileOption, outputFileOption);
        
        queryCommand.SetHandler(async (graphFile, seedFiles) =>
        {
            await QueryGraph(graphFile.FullName, seedFiles);
        }, graphFileOption, seedFilesOption);

        return await rootCommand.InvokeAsync(args);
    }


    // ------------------------------------------------------------------
    //  DEFINE THE CORE LOGIC
    // ------------------------------------------------------------------

   private static async Task BuildGraph(string projectsFilePath, string outputPath)
    {
        var projectPaths = await File.ReadAllLinesAsync(projectsFilePath);
        Console.Error.WriteLine($"Starting to build code graph for {projectPaths.Length} projects...");

        var codeSymbols = new Dictionary<string, CodeSymbol>();
        var symbolCompilations = new Dictionary<Project, Compilation>();

        try
        {
            using var workspace = MSBuildWorkspace.Create();
            
            // --- NEW: Stateful loading logic to handle shared dependencies ---
            var projectsToLoad = new Queue<string>(projectPaths);
            var loadedProjectPaths = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

            while (projectsToLoad.Any())
            {
                var projectPath = projectsToLoad.Dequeue();
                if (loadedProjectPaths.Contains(projectPath) || !File.Exists(projectPath))
                {
                    continue;
                }

                Console.Error.WriteLine($"Loading project: {projectPath}");
                await workspace.OpenProjectAsync(projectPath);

                // After loading, update our set with ALL projects now in the workspace,
                // as OpenProjectAsync loads dependencies automatically.
                foreach (var p in workspace.CurrentSolution.Projects)
                {
                    if (p.FilePath != null)
                    {
                        loadedProjectPaths.Add(p.FilePath);
                    }
                }
            }
            
            var solution = workspace.CurrentSolution;
            // --- END NEW LOGIC ---

            if (workspace.Diagnostics.Any())
            {
                foreach (var diagnostic in workspace.Diagnostics)
                {
                    Console.Error.WriteLine($"Workspace diagnostic: {diagnostic.Message}");
                }
            }

            foreach (var project in solution.Projects)
            {
                Console.Error.WriteLine($"Processing project symbols: {project.Name}");
                var compilation = await project.GetCompilationAsync();
                if (compilation == null) continue;
                symbolCompilations[project] = compilation;
                
                foreach (var document in project.Documents)
                {
                    var syntaxTree = await document.GetSyntaxTreeAsync();
                    if (syntaxTree == null) continue;
                    var semanticModel = compilation.GetSemanticModel(syntaxTree);
                    var root = await syntaxTree.GetRootAsync();
                    ProcessClassesAndInterfaces(root, semanticModel, document.FilePath, codeSymbols);
                }
            }
            
            Console.Error.WriteLine("Processing relationships...");
            foreach (var project in solution.Projects)
            {
                if (!symbolCompilations.TryGetValue(project, out var compilation)) continue;
                foreach (var document in project.Documents)
                {
                    var syntaxTree = await document.GetSyntaxTreeAsync();
                    if (syntaxTree == null) continue;
                    var semanticModel = compilation.GetSemanticModel(syntaxTree);
                    var root = await syntaxTree.GetRootAsync();
                    ProcessRelationships(root, semanticModel, codeSymbols);
                }
            }
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"An unhandled exception occurred: {ex.ToString()}");
            return;
        }
        
        var codeGraph = new CodeGraph(codeSymbols.Values.ToList());
        var jsonOutput = JsonSerializer.Serialize(codeGraph, new JsonSerializerOptions { WriteIndented = true });
        await File.WriteAllTextAsync(outputPath, jsonOutput);
        
        Console.Error.WriteLine($"Code graph with {codeSymbols.Count} symbols saved to: {outputPath}");
    }
    // ------------------------------------------------------------------
    // SYMBOL DISCOVERY METHODS
    // ------------------------------------------------------------------

    /// <summary>
    /// Process all class and interface declarations in the syntax tree
    /// </summary>
    private static void ProcessClassesAndInterfaces(SyntaxNode root, SemanticModel semanticModel,
                                                    string? filePath,  Dictionary<string, CodeSymbol> symbols)
    {
        // Process classes
        foreach (var classDecl in root.DescendantNodes().OfType<ClassDeclarationSyntax>())
        {
            var symbol = semanticModel.GetDeclaredSymbol(classDecl);
            if (symbol == null) continue;

            var location = classDecl.Identifier.GetLocation();
            var lineSpan = location.GetLineSpan();
            var lineNumber = lineSpan.StartLinePosition.Line + 1; // 1-based line number
            var fullName = symbol.ToDisplayString();

            // Create a new code symbol for this class
            var codeSymbol = new CodeSymbol(
                FullName: symbol.ToDisplayString(),
                Kind: SymbolKind.Class,
                FilePath: filePath ?? "unknown",
                LineNumber: lineNumber,
                Relationships: new List<SymbolRelationship>()
            );

            symbols.TryAdd(fullName, codeSymbol);

            // Process methods inside the class
            foreach (var methodDecl in classDecl.DescendantNodes().OfType<MethodDeclarationSyntax>())
            {
                var methodSymbol = semanticModel.GetDeclaredSymbol(methodDecl);
                if (methodSymbol == null) continue;

                var methodLocation = methodDecl.Identifier.GetLocation();
                var methodLineSpan = methodLocation.GetLineSpan();
                var methodLineNumber = methodLineSpan.StartLinePosition.Line + 1;
                var methodFullName = methodSymbol.ToDisplayString();

                // Create a symbol for the method
                var methodCodeSymbol = new CodeSymbol(
                    FullName: methodSymbol.ToDisplayString(),
                    Kind: SymbolKind.Method,
                    FilePath: filePath ?? "unknown",
                    LineNumber: methodLineNumber,
                    Relationships: new List<SymbolRelationship>()
                );

                symbols.TryAdd(methodFullName, methodCodeSymbol);
            }
        }

        // Process interfaces
        foreach (var interfaceDecl in root.DescendantNodes().OfType<InterfaceDeclarationSyntax>())
        {
            var symbol = semanticModel.GetDeclaredSymbol(interfaceDecl);
            if (symbol == null) continue;

            var location = interfaceDecl.Identifier.GetLocation();
            var lineSpan = location.GetLineSpan();
            var lineNumber = lineSpan.StartLinePosition.Line + 1;
            var fullName = symbol.ToDisplayString();

            // Create a new code symbol for this interface
            var codeSymbol = new CodeSymbol(
                FullName: symbol.ToDisplayString(),
                Kind: SymbolKind.Interface,
                FilePath: filePath ?? "unknown",
                LineNumber: lineNumber,
                Relationships: new List<SymbolRelationship>()
            );

            symbols.TryAdd(fullName, codeSymbol);
        }
    }

    /// <summary>
    /// Process relationships between symbols (inheritance, implementation, method calls)
    /// </summary>
    private static void ProcessRelationships(SyntaxNode root, SemanticModel semanticModel, Dictionary<string, CodeSymbol> symbols)
    {
        foreach (var classDecl in root.DescendantNodes().OfType<ClassDeclarationSyntax>())
        {
            var classSymbol = semanticModel.GetDeclaredSymbol(classDecl);
            if (classSymbol == null) continue;
            
            // --- CHANGE: Use fast Dictionary lookup instead of slow FirstOrDefault ---
            if (!symbols.TryGetValue(classSymbol.ToDisplayString(), out var classCodeSymbol)) continue;
            
            if (classSymbol.BaseType != null && !classSymbol.BaseType.Name.Equals("Object")) { /* ... */ }
            foreach (var iface in classSymbol.Interfaces) { /* ... */ }
        }
        
        foreach (var invocation in root.DescendantNodes().OfType<InvocationExpressionSyntax>())
        {
            var symbolInfo = semanticModel.GetSymbolInfo(invocation);
            if (symbolInfo.Symbol == null || !(symbolInfo.Symbol is IMethodSymbol)) continue;
            
            var methodDecl = invocation.Ancestors().OfType<MethodDeclarationSyntax>().FirstOrDefault();
            if (methodDecl == null) continue;
            
            var callingMethodSymbol = semanticModel.GetDeclaredSymbol(methodDecl);
            if (callingMethodSymbol == null) continue;
            
            // --- CHANGE: Use fast Dictionary lookup instead of slow FirstOrDefault ---
            if (!symbols.TryGetValue(callingMethodSymbol.ToDisplayString(), out var callerSymbol)) continue;
            
            var targetMethod = (IMethodSymbol)symbolInfo.Symbol;
            callerSymbol.Relationships.Add(new SymbolRelationship(targetMethod.ToDisplayString(), RelationshipKind.Calls));
        }
    }
    private static async Task QueryGraph(string graphPath, string[] seedFiles)
    {
        // 1. Load the pre-built graph
        if (!File.Exists(graphPath))
        {
            Console.Error.WriteLine($"Error: Code graph file not found at '{graphPath}'");
            return;
        }
        var jsonContent = await File.ReadAllTextAsync(graphPath);
        var codeGraph = JsonSerializer.Deserialize<CodeGraph>(jsonContent);
        if (codeGraph == null || !codeGraph.Symbols.Any())
        {
            Console.Error.WriteLine("Error: Code graph is empty or invalid.");
            return;
        }

        // 2. Create fast lookup dictionaries for efficient traversal
        var symbolsByFullName = codeGraph.Symbols.ToDictionary(s => s.FullName, s => s);
        var symbolsByFilePath = codeGraph.Symbols
            .GroupBy(s => s.FilePath)
            .ToDictionary(g => g.Key, g => g.ToList());

        // 3. Find all symbols within the seed files
        var seedSymbolNames = new HashSet<string>();
        foreach (var seedFile in seedFiles)
        {
            if (symbolsByFilePath.TryGetValue(seedFile, out var symbols))
            {
                foreach (var symbol in symbols)
                {
                    seedSymbolNames.Add(symbol.FullName);
                }
            }
        }

        // 4. Traverse the graph to find all related files
        var finalFilePaths = new HashSet<string>(seedFiles);

        // --- NEW: Perform a reverse search to find what USES the seed symbols ---
        foreach (var symbol in codeGraph.Symbols)
        {
            foreach (var relationship in symbol.Relationships)
            {
                // If any symbol has a relationship pointing to one of our seeds...
                if (seedSymbolNames.Contains(relationship.TargetSymbolFullName))
                {
                    // ...then that symbol's file is also relevant.
                    finalFilePaths.Add(symbol.FilePath);
                }
            }
        }
        
        // 5. Output the final list of related files as JSON
        var jsonOutput = JsonSerializer.Serialize(finalFilePaths);
        Console.WriteLine(jsonOutput);
    }
}
