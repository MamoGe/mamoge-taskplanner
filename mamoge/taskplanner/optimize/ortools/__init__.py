from abc import abstractmethod
import networkx as nx

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp


class ORTaskOptimizer():


    def __init__(self) -> None:
        self.dag = None
        self.manager: pywrapcp.RoutingIndexManager = None
        self.distance_callback_counter = 0
        self.distance_callback_counter_fail = 0
        pass

    def set_dag(self, G:nx.Graph)-> None:
        """set the problem graph to be optimized"""
        self.dag = G


# Create and register a transit callback.
    def distance_callback(self, from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.

        try:
            from_node = self.manager.IndexToNode(from_index)
            to_node = self.manager.IndexToNode(to_index)

            self.distance_callback_counter += 1

            try:
                v = self.dag[from_node][to_node]["distance"]
                #print("distance callback", from_node, to_node, v)
                return v
            except Exception as e:
                self.distance_callback_counter_fail += 1
                #breakpoint()
                #print("distance callback", from_node, to_node, e)
                return 10000000
        except Exception as e:
            print("Exception", e)
            return 10000000

    @abstractmethod
    def solve(self, time=30):
        """Solve the optimization problem"""
        num_nodes = len(self.dag.nodes)
        num_routes = 1
        node_start = 0
        node_end = list(self.dag.nodes)[-1]

        self.manager = pywrapcp.RoutingIndexManager(num_nodes, num_routes, [node_start],[node_end])

        self.routing = pywrapcp.RoutingModel(self.manager)

        cb = lambda x,y: self.distance_callback(x,y)

        transit_callback_index = self.routing.RegisterTransitCallback(cb)

        # Define cost of each arc.
        self.routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
        search_parameters.local_search_metaheuristic = (routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
        search_parameters.time_limit.FromSeconds(time)

        assignment = self.routing.SolveWithParameters(search_parameters)


        return self.extract_solution(num_routes, self.manager, self.routing, assignment)


    def extract_solution(self, num_routes, manager, routing, solution):
        """Prints solution on console."""
        # print(f'Objective: {solution.ObjectiveValue()}')

        results = []
        # max_route_distance = 0
        for vehicle_id in range(num_routes):
            route = []
            index = routing.Start(vehicle_id)
            # plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
            # route_distance = 0
            while not routing.IsEnd(index):
                route.append(manager.IndexToNode(index))
                # plan_output += ' {} -> '.format(manager.IndexToNode(index))
                # previous_index = index
                index = solution.Value(routing.NextVar(index))
                # route_distance += routing.GetArcCostForVehicle(
                    # previous_index, index, vehicle_id)
            results.append(route)

            # plan_output += '{}\n'.format(manager.IndexToNode(index))
            # plan_output += 'Distance of the route: {}m\n'.format(route_distance)
            # print(plan_output)
            # max_route_distance = max(route_distance, max_route_distance)
        #print('Maximum of the route distances: {}m'.format(max_route_distance))
        return results