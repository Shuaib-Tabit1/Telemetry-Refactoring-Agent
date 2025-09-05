"""
Advanced Code Graph Analysis with architectural pattern recognition and dependency analysis.
"""
import json
import networkx as nx
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import subprocess
import tempfile
from .code_graph_manager import code_graph_manager

class RelationshipType(Enum):
    INHERITANCE = "inheritance"
    IMPLEMENTATION = "implementation"
    COMPOSITION = "composition"
    DEPENDENCY = "dependency"
    CALL = "call"
    CONFIGURATION = "configuration"

class ArchitecturalPattern(Enum):
    MIDDLEWARE = "middleware"
    FACTORY = "factory"
    SINGLETON = "singleton"
    DEPENDENCY_INJECTION = "dependency_injection"
    OBSERVER = "observer"
    CHAIN_OF_RESPONSIBILITY = "chain_of_responsibility"

@dataclass
class CodeCluster:
    """Represents a cluster of related code files."""
    name: str
    files: List[Path]
    relationships: Dict[str, List[str]]
    architectural_patterns: List[ArchitecturalPattern]
    entry_points: List[str]
    configuration_files: List[Path]
    test_coverage: float
    complexity_score: int

@dataclass
class ImpactAnalysis:
    """Analysis of potential impact of changes."""
    direct_impact: List[Path]
    indirect_impact: List[Path]
    risk_score: int
    affected_patterns: List[ArchitecturalPattern]
    breaking_changes: List[str]
    test_requirements: List[str]

class AdvancedCodeGraphAnalyzer:
    """Advanced code graph analysis with pattern recognition and impact analysis."""
    
    def __init__(self, code_graph_path: str, roslyn_tool_path: str):
        self.code_graph_path = code_graph_path
        self.roslyn_tool_path = Path(roslyn_tool_path).expanduser()
        
        # Use shared code graph manager
        self.code_graph_data = None
        self.graph = None
        self.symbols_by_file = {}
        self.call_graph = None
        self.dependency_graph = None
        
    def load_and_analyze_graph(self) -> None:
        """Load the code graph and perform advanced analysis."""
        print(f"[DEBUG] AdvancedCodeGraphAnalyzer.load_and_analyze_graph: Loading from {self.code_graph_path}")
        self.code_graph_data = code_graph_manager.get_graph_data(self.code_graph_path)
        
        if self.code_graph_data:
            print(f"[DEBUG] AdvancedCodeGraphAnalyzer.load_and_analyze_graph: Successfully loaded cached data")
            # Use cached data from manager
            self.graph = self.code_graph_data.networkx_graph
            self.symbols_by_file = self.code_graph_data.symbols_by_file
            self.call_graph = self.code_graph_data.call_graph
            self.dependency_graph = self.code_graph_data.dependency_graph
            print(f"[DEBUG] AdvancedCodeGraphAnalyzer.load_and_analyze_graph: Graph has {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
            print(f"[DEBUG] AdvancedCodeGraphAnalyzer.load_and_analyze_graph: symbols_by_file has {len(self.symbols_by_file)} files")
            print(f"[DEBUG] AdvancedCodeGraphAnalyzer.load_and_analyze_graph: Call graph has {self.call_graph.number_of_nodes()} nodes")
            print(f"[DEBUG] AdvancedCodeGraphAnalyzer.load_and_analyze_graph: Dependency graph has {self.dependency_graph.number_of_nodes()} nodes")
        else:
            print(f"[DEBUG] AdvancedCodeGraphAnalyzer.load_and_analyze_graph: Warning: Could not load code graph from {self.code_graph_path}")
            print(f"Warning: Could not load code graph from {self.code_graph_path}")
            # Initialize empty structures
            self.graph = nx.DiGraph()
            self.symbols_by_file = {}
            self.call_graph = nx.DiGraph()
            self.dependency_graph = nx.DiGraph()
    
    def find_architectural_patterns(self, files: List[Path]) -> List[ArchitecturalPattern]:
        """Identify architectural patterns in the given files."""
        patterns = []
        
        for file_path in files:
            file_str = str(file_path)
            file_symbols = self.symbols_by_file.get(file_str, [])
            
            # Pattern detection logic
            if self._is_middleware_pattern(file_symbols, file_str):
                patterns.append(ArchitecturalPattern.MIDDLEWARE)
            
            if self._is_factory_pattern(file_symbols, file_str):
                patterns.append(ArchitecturalPattern.FACTORY)
            
            if self._is_dependency_injection_pattern(file_symbols, file_str):
                patterns.append(ArchitecturalPattern.DEPENDENCY_INJECTION)
            
            if self._is_singleton_pattern(file_symbols, file_str):
                patterns.append(ArchitecturalPattern.SINGLETON)
        
        return list(set(patterns))
    
    def analyze_telemetry_patterns(self, files: List[Path]) -> Dict[str, Any]:
        """Analyze existing telemetry patterns to guide implementation strategy."""
        print(f"[DEBUG] AdvancedCodeGraphAnalyzer.analyze_telemetry_patterns: Analyzing {len(files)} files for telemetry patterns")
        
        telemetry_analysis = {
            "existing_enrichment_files": [],
            "semantic_convention_files": [],
            "implementation_strategy": "create_new",  # default
            "extend_files": []
        }
        
        for file_path in files:
            file_str = str(file_path)
            file_symbols = self.symbols_by_file.get(file_str, [])
            
            if self._is_existing_telemetry_enrichment_pattern(file_symbols, file_str):
                telemetry_analysis["existing_enrichment_files"].append(file_str)
                print(f"[DEBUG] AdvancedCodeGraphAnalyzer.analyze_telemetry_patterns: Found existing enrichment in {file_str}")
            
            if self._is_semantic_conventions_pattern(file_symbols, file_str):
                telemetry_analysis["semantic_convention_files"].append(file_str)
                print(f"[DEBUG] AdvancedCodeGraphAnalyzer.analyze_telemetry_patterns: Found semantic conventions in {file_str}")
        
        # Determine implementation strategy
        if telemetry_analysis["existing_enrichment_files"]:
            telemetry_analysis["implementation_strategy"] = "extend_existing"
            telemetry_analysis["extend_files"] = telemetry_analysis["existing_enrichment_files"]
            print(f"[DEBUG] AdvancedCodeGraphAnalyzer.analyze_telemetry_patterns: Strategy: extend_existing")
        else:
            print(f"[DEBUG] AdvancedCodeGraphAnalyzer.analyze_telemetry_patterns: Strategy: create_new")
        
        return telemetry_analysis
    
    def _is_middleware_pattern(self, symbols: List[Dict], file_path: str) -> bool:
        """Detect middleware pattern."""
        middleware_indicators = [
            "Middleware" in file_path,
            "Pipeline" in file_path,
            any("IMiddleware" in str(s.get("FullName", "")) for s in symbols),
            any("Configure" in str(s.get("FullName", "")) for s in symbols),
            any("app.Use" in str(r.get("TargetSymbolFullName", "")) 
                for s in symbols for r in s.get("Relationships", []))
        ]
        return sum(middleware_indicators) >= 2
    
    def _is_factory_pattern(self, symbols: List[Dict], file_path: str) -> bool:
        """Detect factory pattern."""
        return (
            "Factory" in file_path or
            any("Factory" in str(s.get("FullName", "")) for s in symbols) or
            any("Create" in str(s.get("FullName", "")) for s in symbols if s.get("Kind") == "Method")
        )
    
    def _is_dependency_injection_pattern(self, symbols: List[Dict], file_path: str) -> bool:
        """Detect dependency injection pattern."""
        di_indicators = [
            "Extensions.cs" in file_path,
            "ServiceCollection" in file_path,
            any("IServiceCollection" in str(s.get("FullName", "")) for s in symbols),
            any("AddScoped" in str(r.get("TargetSymbolFullName", "")) 
                for s in symbols for r in s.get("Relationships", [])),
            any("AddSingleton" in str(r.get("TargetSymbolFullName", "")) 
                for s in symbols for r in s.get("Relationships", []))
        ]
        return sum(di_indicators) >= 2
    
    def _is_singleton_pattern(self, symbols: List[Dict], file_path: str) -> bool:
        """Detect singleton pattern."""
        return any("Instance" in str(s.get("FullName", "")) for s in symbols)
    
    def _is_existing_telemetry_enrichment_pattern(self, symbols: List[Dict], file_path: str) -> bool:
        """Detect if this file already has telemetry enrichment that should be extended."""
        print(f"[DEBUG] AdvancedCodeGraphAnalyzer._is_existing_telemetry_enrichment_pattern: Checking {file_path}")
        
        symbol_names = [s.get("FullName", "") for s in symbols]
        print(f"[DEBUG] AdvancedCodeGraphAnalyzer._is_existing_telemetry_enrichment_pattern: Found {len(symbol_names)} symbols")
        
        # Look for existing telemetry calls (various frameworks)
        existing_telemetry_calls = any(
            "SetTag" in name or "SetAttribute" in name or "AddEnrichment" in name or
            "LogEvent" in name or "AddCounter" in name or "RecordValue" in name or
            "TrackEvent" in name or "TrackMetric" in name  # Application Insights patterns
            for name in symbol_names
        )
        
        # Look for telemetry enrichment/callback patterns (various frameworks)
        has_enrichment_patterns = any(
            "EnrichWith" in name or "Enrich" in name or
            "AddInstrumentation" in name or "ConfigureInstrumentation" in name or
            "TelemetryInitializer" in name or "TelemetryProcessor" in name
            for name in symbol_names
        )
        
        # Look for telemetry framework imports and core types
        has_telemetry_patterns = any(
            "Activity" in name or "Span" in name or "Trace" in name or
            "OpenTelemetry" in name or "ApplicationInsights" in name or
            "SemanticConventions" in name or "Instrumentation" in name or
            "TelemetryClient" in name or "ILogger" in name
            for name in symbol_names
        )
        
        # Check file path for telemetry indicators
        telemetry_file_indicators = any(term in file_path.lower() for term in [
            "startup", "application", "middleware", "telemetry", "monitoring", 
            "instrumentation", "tracing", "logging"
        ])
        
        # Prioritize enrichment patterns, but recognize all telemetry infrastructure
        result = (has_enrichment_patterns or existing_telemetry_calls) and (has_telemetry_patterns or telemetry_file_indicators)
        print(f"[DEBUG] AdvancedCodeGraphAnalyzer._is_existing_telemetry_enrichment_pattern: existing_calls={existing_telemetry_calls}, enrichment_patterns={has_enrichment_patterns}, telemetry_patterns={has_telemetry_patterns}, file_indicators={telemetry_file_indicators}, result={result}")
        
        return result
    
    def _is_semantic_conventions_pattern(self, symbols: List[Dict], file_path: str) -> bool:
        """Detect if this file contains semantic conventions or constants that should be extended."""
        print(f"[DEBUG] AdvancedCodeGraphAnalyzer._is_semantic_conventions_pattern: Checking {file_path}")
        
        # Check file name patterns
        file_name = file_path.lower()
        is_conventions_file = any(term in file_name for term in [
            "semantic", "conventions", "constants", "otel", "telemetry"
        ])
        
        # Look for constant/static field patterns
        has_constants = any(
            s.get("Kind") == 6 and  # Field kind
            any(modifier in str(s.get("Modifiers", [])) for modifier in ["Static", "Const", "ReadOnly"])
            for s in symbols
        )
        
        # Look for HTTP-related constants
        symbol_names = [s.get("FullName", "") for s in symbols]
        has_http_constants = any(
            "HTTP" in name.upper() or "HEADER" in name.upper()
            for name in symbol_names
        )
        
        result = is_conventions_file and (has_constants or has_http_constants)
        print(f"[DEBUG] AdvancedCodeGraphAnalyzer._is_semantic_conventions_pattern: conventions_file={is_conventions_file}, has_constants={has_constants}, http_constants={has_http_constants}, result={result}")
        
        return result
    
    def analyze_impact(self, seed_files: List[Path], intent: Dict) -> ImpactAnalysis:
        """Perform comprehensive impact analysis."""
        print(f"[DEBUG] AdvancedCodeGraphAnalyzer.analyze_impact: Analyzing impact for {len(seed_files)} seed files")
        print(f"[DEBUG] AdvancedCodeGraphAnalyzer.analyze_impact: Seed files: {[str(f) for f in seed_files]}")
        
        if not self.dependency_graph:
            print(f"[DEBUG] AdvancedCodeGraphAnalyzer.analyze_impact: No dependency graph available, returning empty analysis")
            return ImpactAnalysis([], [], 0, [], [], [])
        
        print(f"[DEBUG] AdvancedCodeGraphAnalyzer.analyze_impact: Dependency graph has {self.dependency_graph.number_of_nodes()} nodes")
        
        direct_impact = set(str(f) for f in seed_files)
        indirect_impact = set()
        
        # Find all files that depend on seed files
        for seed_file in seed_files:
            seed_str = str(seed_file)
            print(f"[DEBUG] AdvancedCodeGraphAnalyzer.analyze_impact: Processing seed file: {seed_str}")
            if seed_str in self.dependency_graph:
                print(f"[DEBUG] AdvancedCodeGraphAnalyzer.analyze_impact: Seed file found in dependency graph")
                # Find predecessors (files that depend on this file)
                predecessors = set(self.dependency_graph.predecessors(seed_str))
                print(f"[DEBUG] AdvancedCodeGraphAnalyzer.analyze_impact: Found {len(predecessors)} predecessors")
                indirect_impact.update(predecessors)
                
                # Find successors (files this file depends on)
                successors = set(self.dependency_graph.successors(seed_str))
                print(f"[DEBUG] AdvancedCodeGraphAnalyzer.analyze_impact: Found {len(successors)} successors")
                indirect_impact.update(successors)
            else:
                print(f"[DEBUG] AdvancedCodeGraphAnalyzer.analyze_impact: Seed file NOT found in dependency graph")
        
        # Remove direct impact from indirect impact
        indirect_impact -= direct_impact
        print(f"[DEBUG] AdvancedCodeGraphAnalyzer.analyze_impact: Direct impact: {len(direct_impact)} files, Indirect impact: {len(indirect_impact)} files")
        
        # Calculate risk score based on various factors
        risk_score = self._calculate_risk_score(
            len(direct_impact), len(indirect_impact), intent
        )
        print(f"[DEBUG] AdvancedCodeGraphAnalyzer.analyze_impact: Calculated risk score: {risk_score}")
        
        # Identify affected architectural patterns
        all_affected_files = [Path(f) for f in direct_impact | indirect_impact]
        affected_patterns = self.find_architectural_patterns(all_affected_files)
        
        # Identify potential breaking changes
        breaking_changes = self._identify_breaking_changes(seed_files, intent)
        
        # Suggest test requirements
        test_requirements = self._suggest_test_requirements(all_affected_files, intent)
        
        return ImpactAnalysis(
            direct_impact=[Path(f) for f in direct_impact],
            indirect_impact=[Path(f) for f in indirect_impact],
            risk_score=risk_score,
            affected_patterns=affected_patterns,
            breaking_changes=breaking_changes,
            test_requirements=test_requirements
        )
    
    def _calculate_risk_score(self, direct_count: int, indirect_count: int, intent: Dict) -> int:
        """Calculate risk score from 1-10."""
        base_score = min(direct_count * 2 + indirect_count, 10)
        
        # Adjust based on operation type
        operation = intent.get("telemetry_operation", {})
        if operation.get("action") == "CREATE":
            base_score += 2
        
        # Adjust based on category
        if intent.get("issue_category") == "CONFIGURATION":
            base_score += 1
        
        return min(base_score, 10)
    
    def _identify_breaking_changes(self, seed_files: List[Path], intent: Dict) -> List[str]:
        """Identify potential breaking changes."""
        breaking_changes = []
        
        operation = intent.get("telemetry_operation", {})
        if operation.get("action") == "CREATE":
            breaking_changes.append("New instrumentation may affect performance")
        
        for file_path in seed_files:
            if "Startup.cs" in str(file_path):
                breaking_changes.append("Startup configuration changes may affect application boot")
            
            if "Extensions.cs" in str(file_path):
                breaking_changes.append("Service registration changes may affect dependency injection")
        
        return breaking_changes
    
    def _suggest_test_requirements(self, affected_files: List[Path], intent: Dict) -> List[str]:
        """Suggest test requirements based on impact analysis."""
        test_requirements = []
        
        # Basic test requirements
        test_requirements.append("Unit tests for modified methods")
        test_requirements.append("Integration tests for telemetry data collection")
        
        # Pattern-specific test requirements
        for file_path in affected_files:
            if "Middleware" in str(file_path):
                test_requirements.append("Middleware pipeline integration tests")
            
            if "Extensions.cs" in str(file_path):
                test_requirements.append("Service registration validation tests")
        
        # Operation-specific test requirements
        operation = intent.get("telemetry_operation", {})
        if operation.get("type") == "span":
            test_requirements.append("OpenTelemetry span validation tests")
        elif operation.get("type") == "metric":
            test_requirements.append("Metrics collection validation tests")
        
        return list(set(test_requirements))
    
    def create_code_clusters(self, all_files: List[Path]) -> List[CodeCluster]:
        """Create logical clusters of related code files."""
        clusters = []
        processed_files = set()
        
        for file_path in all_files:
            if str(file_path) in processed_files:
                continue
            
            # Find all files strongly connected to this file
            cluster_files = self._find_connected_files(file_path, all_files)
            
            if len(cluster_files) > 1:
                cluster_name = self._generate_cluster_name(cluster_files)
                patterns = self.find_architectural_patterns(cluster_files)
                
                cluster = CodeCluster(
                    name=cluster_name,
                    files=cluster_files,
                    relationships=self._analyze_cluster_relationships(cluster_files),
                    architectural_patterns=patterns,
                    entry_points=self._find_entry_points(cluster_files),
                    configuration_files=self._find_configuration_files(cluster_files),
                    test_coverage=0.0,  # Could be enhanced with actual coverage data
                    complexity_score=len(cluster_files)
                )
                
                clusters.append(cluster)
                processed_files.update(str(f) for f in cluster_files)
        
        return clusters
    
    def _find_connected_files(self, seed_file: Path, all_files: List[Path]) -> List[Path]:
        """Find files strongly connected to the seed file."""
        if not self.dependency_graph:
            return [seed_file]
        
        seed_str = str(seed_file)
        connected = {seed_str}
        
        # Add direct dependencies
        if seed_str in self.dependency_graph:
            connected.update(self.dependency_graph.successors(seed_str))
            connected.update(self.dependency_graph.predecessors(seed_str))
        
        # Filter to only include files in our analysis set
        all_files_str = {str(f) for f in all_files}
        connected = connected.intersection(all_files_str)
        
        return [Path(f) for f in connected]
    
    def _generate_cluster_name(self, files: List[Path]) -> str:
        """Generate a meaningful name for a code cluster."""
        # Extract common patterns from file names
        names = [f.stem for f in files]
        
        # Look for common prefixes or patterns
        if any("Extension" in name for name in names):
            return "Configuration Extensions"
        elif any("Middleware" in name for name in names):
            return "Middleware Pipeline"
        elif any("Service" in name for name in names):
            return "Service Layer"
        else:
            return f"Cluster ({len(files)} files)"
    
    def _analyze_cluster_relationships(self, files: List[Path]) -> Dict[str, List[str]]:
        """Analyze relationships within a cluster."""
        relationships = {}
        
        for file_path in files:
            file_str = str(file_path)
            relationships[file_str] = []
            
            if self.dependency_graph and file_str in self.dependency_graph:
                # Find relationships to other files in the cluster
                cluster_files = {str(f) for f in files}
                for successor in self.dependency_graph.successors(file_str):
                    if successor in cluster_files:
                        relationships[file_str].append(successor)
        
        return relationships
    
    def _find_entry_points(self, files: List[Path]) -> List[str]:
        """Find entry points (public APIs) in a cluster."""
        entry_points = []
        
        for file_path in files:
            file_symbols = self.symbols_by_file.get(str(file_path), [])
            for symbol in file_symbols:
                # Look for public methods that might be entry points
                if (symbol.get("Kind") == "Method" and 
                    ("public" in str(symbol.get("FullName", "")).lower() or
                     "Configure" in str(symbol.get("FullName", "")) or
                     "Add" in str(symbol.get("FullName", "")))):
                    entry_points.append(symbol["FullName"])
        
        return entry_points
    
    def _find_configuration_files(self, files: List[Path]) -> List[Path]:
        """Find configuration files within a cluster."""
        config_patterns = ["appsettings", "config", "startup", "program"]
        
        return [
            f for f in files
            if any(pattern in str(f).lower() for pattern in config_patterns)
        ]
    
    def get_file_relationships(self, file_path: Path, relationship_types: List[str] = None, max_depth: int = 1) -> Dict[str, List[str]]:
        """
        Get relationships for a specific file from the code graph.
        
        Args:
            file_path: The file to analyze relationships for
            relationship_types: Types of relationships to include ['calls', 'called_by', 'dependencies', 'inheritance']
            max_depth: How deep to traverse relationships (currently only depth 1 supported)
            
        Returns:
            Dict with relationship types as keys and lists of related file paths as values
        """
        if relationship_types is None:
            relationship_types = ['calls', 'called_by']
        
        relationships = {}
        file_str = str(file_path)
        
        print(f"[DEBUG] get_file_relationships: Analyzing {file_str}")
        print(f"[DEBUG] get_file_relationships: Call graph has {self.call_graph.number_of_nodes() if self.call_graph else 0} nodes")
        print(f"[DEBUG] get_file_relationships: Dependency graph has {self.dependency_graph.number_of_nodes() if self.dependency_graph else 0} nodes")
        
        # Initialize empty lists for all requested relationship types
        for rel_type in relationship_types:
            relationships[rel_type] = []
        
        if not self.call_graph or not self.dependency_graph:
            print(f"[DEBUG] get_file_relationships: No graphs available, returning empty relationships")
            return relationships
        
        # Get direct calls (what this file calls)
        if 'calls' in relationship_types and file_str in self.call_graph:
            calls = []
            for target in self.call_graph.successors(file_str):
                calls.append(target)
            relationships['calls'] = calls[:5]  # Limit to avoid overwhelming context
            print(f"[DEBUG] get_file_relationships: Found {len(calls)} calls, limited to {len(relationships['calls'])}")
        
        # Get called_by (what calls this file)  
        if 'called_by' in relationship_types and file_str in self.call_graph:
            called_by = []
            for source in self.call_graph.predecessors(file_str):
                called_by.append(source)
            relationships['called_by'] = called_by[:5]  # Limit to avoid overwhelming context
            print(f"[DEBUG] get_file_relationships: Found {len(called_by)} called_by, limited to {len(relationships['called_by'])}")
        
        # Add dependency relationships if requested
        if 'dependencies' in relationship_types and file_str in self.dependency_graph:
            deps = []
            for target in self.dependency_graph.successors(file_str):
                deps.append(target)
            relationships['dependencies'] = deps[:5]  # Limit to avoid overwhelming context
            print(f"[DEBUG] get_file_relationships: Found {len(deps)} dependencies, limited to {len(relationships['dependencies'])}")
        
        # Add inheritance relationships if requested
        if 'inheritance' in relationship_types:
            # For inheritance, we'd need to analyze the symbols, this is a simplified version
            inheritance = []
            file_symbols = self.symbols_by_file.get(file_str, [])
            for symbol in file_symbols:
                if symbol.get('kind') == 'class' and 'base_types' in symbol:
                    # This would require more sophisticated analysis
                    pass
            relationships['inheritance'] = inheritance
        
        total_related = sum(len(rel_list) for rel_list in relationships.values())
        print(f"[DEBUG] get_file_relationships: Total relationships found: {total_related}")
        
        return relationships
