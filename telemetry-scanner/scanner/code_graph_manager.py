"""
Shared Code Graph Manager to avoid duplicate loading and processing.
"""
import json
from pathlib import Path
from typing import Dict, Optional, Any, Union
import networkx as nx
from dataclasses import dataclass

@dataclass
class CodeGraphData:
    """Cached code graph data structures."""
    raw_data: Dict[str, Any]
    networkx_graph: nx.DiGraph
    symbols_by_file: Dict[str, list]
    call_graph: nx.DiGraph
    dependency_graph: nx.DiGraph

class CodeGraphManager:
    """Singleton manager for code graph data to avoid duplicate loading."""
    
    _instance = None
    _cached_data: Optional[CodeGraphData] = None
    _cached_path: Optional[str] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize the graph cache dictionary
            cls._instance._graph_cache = {}
        return cls._instance
    
    def get_graph_data(self, graph_path: Union[Path, str]) -> Optional[CodeGraphData]:
        """Get cached graph data for a given path"""
        print(f"[DEBUG] CodeGraphManager.get_graph_data: Requested path: {graph_path}")
        
        # Ensure graph_path is a Path object
        if isinstance(graph_path, str):
            graph_path = Path(graph_path)
        
        graph_path_str = str(graph_path)
        
        if graph_path_str in self._graph_cache:
            print(f"[DEBUG] CodeGraphManager.get_graph_data: Found cached data for {graph_path}")
            return self._graph_cache[graph_path_str]
        
        print(f"[DEBUG] CodeGraphManager.get_graph_data: No cached data, checking file existence")
        if not graph_path.exists():
            print(f"[DEBUG] CodeGraphManager.get_graph_data: File does not exist: {graph_path}")
            return None
        
        try:
            print(f"[DEBUG] CodeGraphManager.get_graph_data: Loading graph data from file")
            # Load and cache the graph data
            with open(graph_path, 'r') as f:
                raw_data = json.load(f)
            
            print(f"[DEBUG] CodeGraphManager.get_graph_data: Creating CodeGraphData object")
            # Build all the graph structures
            networkx_graph = self._build_networkx_graph(raw_data)
            symbols_by_file = self._group_symbols_by_file(raw_data)
            call_graph = self._build_call_graph(raw_data)
            dependency_graph = self._build_dependency_graph(raw_data)
            
            graph_data = CodeGraphData(
                raw_data=raw_data,
                networkx_graph=networkx_graph,
                symbols_by_file=symbols_by_file,
                call_graph=call_graph,
                dependency_graph=dependency_graph
            )
            print(f"[DEBUG] CodeGraphManager.get_graph_data: Caching graph data for {graph_path}")
            self._graph_cache[graph_path_str] = graph_data
            print(f"[DEBUG] CodeGraphManager.get_graph_data: Successfully loaded and cached graph data")
            return graph_data
            
        except Exception as e:
            print(f"[DEBUG] CodeGraphManager.get_graph_data: Error loading graph from {graph_path}: {e}")
            print(f"Error loading graph from {graph_path}: {e}")
            return None
    
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
    
    def _group_symbols_by_file(self, graph_data: Dict) -> Dict[str, list]:
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
            if symbol["Kind"] == 2:  # Method kind
                call_graph.add_node(symbol["FullName"], **symbol)
                
                for relationship in symbol.get("Relationships", []):
                    if relationship["Kind"] == 2:  # Calls relationship
                        call_graph.add_edge(
                            symbol["FullName"],
                            relationship["TargetSymbolFullName"]
                        )
        
        return call_graph
    
    def _build_dependency_graph(self, graph_data: Dict) -> nx.DiGraph:
        """Build a file-level dependency graph."""
        dependency_graph = nx.DiGraph()
        
        # Group symbols by file
        symbols_by_file = self._group_symbols_by_file(graph_data)
        
        # Add nodes for each file
        for file_path in symbols_by_file.keys():
            dependency_graph.add_node(file_path)
        
        # Add edges based on symbol relationships across files
        for file_path, symbols in symbols_by_file.items():
            for symbol in symbols:
                for relationship in symbol.get("Relationships", []):
                    # Find the target symbol's file
                    target_symbol = relationship["TargetSymbolFullName"]
                    for target_file, target_symbols in symbols_by_file.items():
                        if target_file != file_path:  # Different file
                            target_names = [s["FullName"] for s in target_symbols]
                            if target_symbol in target_names:
                                dependency_graph.add_edge(file_path, target_file)
                                break
        
        return dependency_graph
    
    def clear_cache(self):
        """Clear cached data to force reload."""
        self._cached_data = None
        self._cached_path = None

# Global instance
code_graph_manager = CodeGraphManager()
