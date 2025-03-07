"""
Dependency Manager
Module for managing dependencies between script components
"""

import os
import json
import networkx as nx
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from pathlib import Path


class DependencyManager:
    """
    Manages dependencies between script components and determines optimal generation order
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the dependency manager
        
        Args:
            config: Configuration dictionary with dependency management settings
        """
        self.config = config or {}
        
    def analyze_dependencies(self, components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze dependencies between components and create a dependency graph
        
        Args:
            components: List of component definitions
            
        Returns:
            Dictionary containing dependency analysis results
        """
        # Create dependency graph
        dependency_graph = self._create_dependency_graph(components)
        
        # Create NetworkX graph for advanced analysis
        G = self._create_networkx_graph(dependency_graph)
        
        # Determine generation order
        generation_order = self._determine_generation_order(G)
        
        # Identify critical path
        critical_path = self._identify_critical_path(G, generation_order)
        
        # Check for cycles
        cycles = list(nx.simple_cycles(G))
        
        # Identify strongly connected components
        strongly_connected = list(nx.strongly_connected_components(G))
        
        return {
            "dependency_graph": dependency_graph,
            "generation_order": generation_order,
            "critical_path": critical_path,
            "has_cycles": len(cycles) > 0,
            "cycles": cycles,
            "strongly_connected_components": [list(component) for component in strongly_connected],
            "complexity": self._calculate_dependency_complexity(G)
        }
    
    def _create_dependency_graph(self, components: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Create a dependency graph from component definitions
        
        Args:
            components: List of component definitions
            
        Returns:
            Dictionary mapping component IDs to their dependencies
        """
        graph = {}
        
        # Create mapping from component name to ID
        name_to_id = {}
        for component in components:
            component_id = component.get("id")
            component_name = component.get("name")
            if component_name:
                name_to_id[component_name] = component_id
            graph[component_id] = []
        
        # Add dependencies
        for component in components:
            component_id = component.get("id")
            dependencies = component.get("depends_on", [])
            
            for dependency in dependencies:
                # Check if dependency is already an ID
                if dependency in graph:
                    dep_id = dependency
                else:
                    # Look up ID by name
                    dep_id = name_to_id.get(dependency)
                
                if dep_id and dep_id != component_id:  # Avoid self-dependencies
                    graph[component_id].append(dep_id)
        
        return graph
    
    def _create_networkx_graph(self, dependency_graph: Dict[str, List[str]]) -> nx.DiGraph:
        """
        Create a NetworkX directed graph from the dependency graph
        
        Args:
            dependency_graph: Dictionary mapping component IDs to their dependencies
            
        Returns:
            NetworkX DiGraph object
        """
        G = nx.DiGraph()
        
        # Add all nodes
        for node in dependency_graph:
            G.add_node(node)
        
        # Add all edges
        for node, dependencies in dependency_graph.items():
            for dep in dependencies:
                G.add_edge(dep, node)  # Edge from dependency to dependent
        
        return G
    
    def _determine_generation_order(self, G: nx.DiGraph) -> List[str]:
        """
        Determine the order in which components should be generated
        
        Args:
            G: NetworkX DiGraph representing the dependency graph
            
        Returns:
            List of component IDs in generation order
        """
        try:
            # Use topological sort for acyclic graphs
            return list(nx.topological_sort(G))
        except nx.NetworkXUnfeasible:
            # Graph has cycles, use approximate approach
            return self._approximate_generation_order(G)
    
    def _approximate_generation_order(self, G: nx.DiGraph) -> List[str]:
        """
        Determine an approximate generation order for graphs with cycles
        
        Args:
            G: NetworkX DiGraph representing the dependency graph
            
        Returns:
            List of component IDs in approximate generation order
        """
        # Break cycles by removing edges with minimum feedback arc set
        feedback_edges = nx.algorithms.minimum_feedback_arc_set(G)
        
        # Create a new graph without the feedback edges
        G_acyclic = G.copy()
        G_acyclic.remove_edges_from(feedback_edges)
        
        # Return the topological sort of the acyclic graph
        return list(nx.topological_sort(G_acyclic))
    
    def _identify_critical_path(self, G: nx.DiGraph, generation_order: List[str]) -> List[str]:
        """
        Identify the critical path through the dependency graph
        
        Args:
            G: NetworkX DiGraph representing the dependency graph
            generation_order: List of component IDs in generation order
            
        Returns:
            List of component IDs forming the critical path
        """
        if not generation_order:
            return []
        
        # Create a weighted graph based on component complexity
        weighted_G = G.copy()
        
        # Assign weights to edges based on approximate component complexity
        for u, v in G.edges():
            weighted_G[u][v]['weight'] = 1
        
        # Find the longest path from any start node to any end node
        start_nodes = [node for node in G.nodes() if G.in_degree(node) == 0]
        end_nodes = [node for node in G.nodes() if G.out_degree(node) == 0]
        
        if not start_nodes or not end_nodes:
            # If no clear start/end nodes, use first and last in generation order
            return [generation_order[0], generation_order[-1]]
        
        # Find the longest path
        longest_path = []
        max_length = -1
        
        for start in start_nodes:
            for end in end_nodes:
                try:
                    path = nx.dag_longest_path(weighted_G, weight='weight', source=start, target=end)
                    length = nx.dag_longest_path_length(weighted_G, weight='weight', source=start, target=end)
                    
                    if length > max_length:
                        max_length = length
                        longest_path = path
                except (nx.NetworkXNoPath, nx.NetworkXError):
                    # No path exists or graph has cycles
                    continue
        
        return longest_path
    
    def _calculate_dependency_complexity(self, G: nx.DiGraph) -> Dict[str, Any]:
        """
        Calculate complexity metrics for the dependency graph
        
        Args:
            G: NetworkX DiGraph representing the dependency graph
            
        Returns:
            Dictionary of complexity metrics
        """
        num_nodes = G.number_of_nodes()
        num_edges = G.number_of_edges()
        
        # Calculate average degree
        if num_nodes > 0:
            avg_in_degree = sum(d for n, d in G.in_degree()) / num_nodes
            avg_out_degree = sum(d for n, d in G.out_degree()) / num_nodes
        else:
            avg_in_degree = 0
            avg_out_degree = 0
        
        # Calculate density
        if num_nodes > 1:
            density = nx.density(G)
        else:
            density = 0
        
        # Calculate diameter (if graph is connected)
        diameter = -1
        try:
            UG = G.to_undirected()
            if nx.is_connected(UG):
                diameter = nx.diameter(UG)
        except nx.NetworkXError:
            # Graph is not connected or has other issues
            pass
        
        return {
            "node_count": num_nodes,
            "edge_count": num_edges,
            "avg_in_degree": avg_in_degree,
            "avg_out_degree": avg_out_degree,
            "density": density,
            "diameter": diameter,
            "is_dag": nx.is_directed_acyclic_graph(G),
            "components": nx.number_strongly_connected_components(G)
        }
    
    def validate_dependencies(self, components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate dependencies between components
        
        Args:
            components: List of component definitions
            
        Returns:
            Dictionary containing validation results
        """
        # Create dependency graph
        dependency_graph = self._create_dependency_graph(components)
        
        # Create NetworkX graph
        G = self._create_networkx_graph(dependency_graph)
        
        # Check for cycles
        cycles = list(nx.simple_cycles(G))
        has_cycles = len(cycles) > 0
        
        # Check for missing dependencies
        missing_dependencies = []
        for component in components:
            component_id = component.get("id")
            dependencies = component.get("depends_on", [])
            
            for dependency in dependencies:
                # Check if dependency ID exists
                if dependency not in dependency_graph:
                    # Check if it's a component name rather than ID
                    found = False
                    for other_component in components:
                        if other_component.get("name") == dependency:
                            found = True
                            break
                    
                    if not found:
                        missing_dependencies.append({
                            "component_id": component_id,
                            "missing_dependency": dependency
                        })
        
        # Check for islands (disconnected components)
        UG = G.to_undirected()
        connected_components = list(nx.connected_components(UG))
        islands = []
        
        if len(connected_components) > 1:
            # Find single-node components
            for component in connected_components:
                if len(component) == 1:
                    islands.extend(list(component))
        
        return {
            "valid": not has_cycles and not missing_dependencies,
            "has_cycles": has_cycles,
            "cycles": cycles,
            "missing_dependencies": missing_dependencies,
            "islands": islands,
            "connected_components": [list(component) for component in connected_components]
        }
    
    def suggest_parallel_execution(self, components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Suggest components that can be executed in parallel
        
        Args:
            components: List of component definitions
            
        Returns:
            Dictionary containing parallelization suggestions
        """
        # Analyze dependencies
        analysis = self.analyze_dependencies(components)
        
        # Create NetworkX graph
        dependency_graph = analysis["dependency_graph"]
        G = self._create_networkx_graph(dependency_graph)
        
        # Get generation order
        generation_order = analysis["generation_order"]
        
        # Group components by their topological "level"
        levels = {}
        for node in G.nodes():
            # Calculate the longest path to this node
            try:
                level = 0
                for predecessor in G.predecessors(node):
                    level = max(level, levels.get(predecessor, 0) + 1)
                levels[node] = level
            except Exception:
                # Fall back to simple approach if error occurs
                levels[node] = len(list(G.predecessors(node)))
        
        # Group nodes by level
        level_groups = {}
        for node, level in levels.items():
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(node)
        
        # Sort groups by level
        parallel_groups = [nodes for level, nodes in sorted(level_groups.items())]
        
        # Get component names for better readability
        component_names = {component.get("id"): component.get("name") for component in components}
        
        named_groups = []
        for group in parallel_groups:
            named_group = [{
                "id": node,
                "name": component_names.get(node, node)
            } for node in group]
            named_groups.append(named_group)
        
        # Calculate maximum parallel workers needed
        max_parallel = max(len(group) for group in parallel_groups) if parallel_groups else 0
        
        return {
            "parallel_groups": named_groups,
            "max_parallel_workers": max_parallel,
            "generation_order": generation_order,
            "level_count": len(parallel_groups)
        }


# Test the dependency manager if run directly
if __name__ == "__main__":
    dependency_manager = DependencyManager()
    
    # Example components
    test_components = [
        {
            "id": "component_0",
            "name": "data_processor_main",
            "type": "main",
            "description": "Main entry point for the data processor",
            "is_primary": True
        },
        {
            "id": "component_1",
            "name": "data_processor_reader",
            "type": "reader",
            "description": "Data input reader"
        },
        {
            "id": "component_2",
            "name": "data_processor_processor",
            "type": "processor",
            "description": "Data processing logic",
            "depends_on": ["data_processor_reader"]
        },
        {
            "id": "component_3",
            "name": "data_processor_writer",
            "type": "writer",
            "description": "Data output writer",
            "depends_on": ["data_processor_processor"]
        },
        {
            "id": "component_4",
            "name": "data_processor_utils",
            "type": "util",
            "description": "Utility functions"
        }
    ]
    
    analysis = dependency_manager.analyze_dependencies(test_components)
    print("Dependency Analysis:")
    print(json.dumps(analysis, indent=2))
    
    validation = dependency_manager.validate_dependencies(test_components)
    print("\nDependency Validation:")
    print(json.dumps(validation, indent=2))
    
    parallel = dependency_manager.suggest_parallel_execution(test_components)
    print("\nParallel Execution Suggestion:")
    print(json.dumps(parallel, indent=2))
