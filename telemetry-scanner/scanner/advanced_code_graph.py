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
        self.graph = None
        self.symbols_by_file = {}
        self.call_graph = None
        self.dependency_graph = None
        
    def load_and_analyze_graph(self) -> None:
        """Load the code graph and perform advanced analysis."""
        with open(self.code_graph_path, 'r') as f:
            graph_data = json.load(f)
        
        # Build NetworkX graph for advanced analysis
        self.graph = self._build_networkx_graph(graph_data)
        self.symbols_by_file = self._group_symbols_by_file(graph_data)
        self.call_graph = self._build_call_graph(graph_data)
        self.dependency_graph = self._build_dependency_graph(graph_data)
    
    def _build_networkx_graph(self, graph_data: Dict) -> nx.DiGraph:
        """Build a NetworkX directed graph from the code graph data."""
        G = nx.DiGraph()
        
        # Add nodes for each symbol
        for symbol in graph_data.get("Symbols", []):
            G.add_node(
                symbol["FullName"],
                kind=symbol["Kind"],
                file_path=symbol["FilePath"],
                line_number=symbol["LineNumber"]
            )
        
        # Add edges for relationships
        for symbol in graph_data.get("Symbols", []):
            for relationship in symbol.get("Relationships", []):
                G.add_edge(
                    symbol["FullName"],
                    relationship["TargetSymbolFullName"],
                    relationship_type=relationship["Kind"]
                )
        
        return G
    
    def _group_symbols_by_file(self, graph_data: Dict) -> Dict[str, List[Dict]]:
        """Group symbols by their file path."""
        symbols_by_file = {}
        for symbol in graph_data.get("Symbols", []):
            file_path = symbol["FilePath"]
            if file_path not in symbols_by_file:
                symbols_by_file[file_path] = []
            symbols_by_file[file_path].append(symbol)
        return symbols_by_file
    
    def _build_call_graph(self, graph_data: Dict) -> nx.DiGraph:
        """Build a call graph showing method invocation relationships."""
        call_graph = nx.DiGraph()
        
        for symbol in graph_data.get("Symbols", []):
            if symbol["Kind"] == "Method":
                call_graph.add_node(symbol["FullName"], **symbol)
                
                for relationship in symbol.get("Relationships", []):
                    if relationship["Kind"] == "Calls":
                        call_graph.add_edge(
                            symbol["FullName"],
                            relationship["TargetSymbolFullName"]
                        )
        
        return call_graph
    
    def _build_dependency_graph(self, graph_data: Dict) -> nx.DiGraph:
        """Build a dependency graph showing file-level dependencies."""
        dep_graph = nx.DiGraph()
        file_dependencies = {}
        
        # Analyze inter-file dependencies
        for symbol in graph_data.get("Symbols", []):
            source_file = symbol["FilePath"]
            
            for relationship in symbol.get("Relationships", []):
                # Find the file containing the target symbol
                target_file = self._find_symbol_file(
                    relationship["TargetSymbolFullName"], graph_data
                )
                
                if target_file and target_file != source_file:
                    if source_file not in file_dependencies:
                        file_dependencies[source_file] = set()
                    file_dependencies[source_file].add(target_file)
        
        # Build the dependency graph
        for source_file, target_files in file_dependencies.items():
            dep_graph.add_node(source_file)
            for target_file in target_files:
                dep_graph.add_node(target_file)
                dep_graph.add_edge(source_file, target_file)
        
        return dep_graph
    
    def _find_symbol_file(self, symbol_name: str, graph_data: Dict) -> Optional[str]:
        """Find the file containing a specific symbol."""
        for symbol in graph_data.get("Symbols", []):
            if symbol["FullName"] == symbol_name:
                return symbol["FilePath"]
        return None
    
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
    
    def analyze_impact(self, seed_files: List[Path], intent: Dict) -> ImpactAnalysis:
        """Perform comprehensive impact analysis."""
        if not self.dependency_graph:
            return ImpactAnalysis([], [], 0, [], [], [])
        
        direct_impact = set(str(f) for f in seed_files)
        indirect_impact = set()
        
        # Find all files that depend on seed files
        for seed_file in seed_files:
            seed_str = str(seed_file)
            if seed_str in self.dependency_graph:
                # Find predecessors (files that depend on this file)
                predecessors = set(self.dependency_graph.predecessors(seed_str))
                indirect_impact.update(predecessors)
                
                # Find successors (files this file depends on)
                successors = set(self.dependency_graph.successors(seed_str))
                indirect_impact.update(successors)
        
        # Remove direct impact from indirect impact
        indirect_impact -= direct_impact
        
        # Calculate risk score based on various factors
        risk_score = self._calculate_risk_score(
            len(direct_impact), len(indirect_impact), intent
        )
        
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
