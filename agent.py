import random
from environment import Agent, Environment, TrafficLight
from planner import RoutePlanner
from simulator import Simulator
import operator

class LearningAgent(Agent):
    """An agent that learns to drive in the smartcab world."""

    def __init__(self, env, trials=1):
        super(LearningAgent, self).__init__(env)  # sets self.env = env, state = None, next_waypoint = None, and a default color
        self.color = 'red'  # override color
        self.planner = RoutePlanner(self.env, self)  # simple route planner to get next_waypoint
        # TODO: Initialize any additional variables here
        # Initialize the value of Q
        self.value_Q = {}
        self.initial_Q = 1

        # Initialize Q-learning parameters
        self.alpha = 0.9
        self.gamma = 0.1
        self.epsilon = 0.0

        # Initialize agent's statistics about learning how to drive
        self.success = 0
        self.nb_attempts = 0
        self.nb_penalties = 0
        self.nb_moves = 0
        self.net_reward = 0

    def reset(self, destination=None):
        self.planner.route_to(destination)
        # TODO: Prepare for a new trip; reset any variables here, if required
        # Initialize the previous state, action and reward
        self.previous_state = None
        self.previous_action = None
        self.previous_reward = None

    def update(self, t):
        # Gather inputs
        self.next_waypoint = self.planner.next_waypoint()  # from route planner, also displayed by simulator
        inputs = self.env.sense(self)
        deadline = self.env.get_deadline(self)

        # TODO: Update state
        self.state = inputs
        self.state['next_waypoint'] = self.next_waypoint
        self.state = tuple(sorted(inputs.items()))
        
        # TODO: Select action according to your policy
        value_Q, action = self.select_Q_action(self.state)

        # Execute action and get reward
        reward = self.env.act(self, action)

        # TODO: Learn policy based on state, action, reward
        if self.previous_state != None:
            if (self.previous_state, self.previous_action) not in self.value_Q:
                self.value_Q[(self.previous_state, self.previous_action)] = self.initial_Q
            self.value_Q[(self.previous_state,self.previous_action)] = (1 - self.alpha) * self.value_Q[(self.previous_state,self.previous_action)] + self.alpha * (self.previous_reward + self.gamma * self.select_Q_action(self.state)[0])

        self.previous_state = self.state
        self.previous_action = action
        self.previous_reward = reward

        # Statistics about the agent
        self.net_reward += reward
        self.nb_moves += 1
        if reward < 0:
            self.nb_penalties += 1

        add_total = False
        if deadline == 0:
            add_total = True
        if reward >= 10:
            self.success += 1
            add_total = True
        if add_total:
            self.nb_attempts += 1
            print self.agent_statistics()
        self.env.status_text += ' ' + self.agent_statistics()

        print "LearningAgent.update(): deadline = {}, inputs = {}, action = {}, reward = {}".format(deadline, inputs, action, reward)  # [debug]

    def agent_statistics(self):
        """Statistics about the agent's attempts, successes and penalties"""
        if self.nb_attempts == 0:
            success_rate = 0
        else:
            success_rate = round(float(self.success)/float(self.nb_attempts), 2)
        penalty_rate = round(float(self.nb_penalties)/float(self.nb_moves), 2)
        return "The success rate is: {}/{} ({})\nThe penalty rate is: {}/{} ({})\nThe net reward is: {}".format(
                self.success, self.nb_attempts, success_rate, self.nb_penalties, self.nb_moves, penalty_rate, self.net_reward)

    def select_Q_action(self, state):
        """Select the maximum Q and best action based on the given state."""
        best_action = random.choice(Environment.valid_actions)
        if random.random() < self.epsilon:
            max_Q = self.get_Q_value(state, best_action)
        else:
            max_Q = float('-inf')
            for action in Environment.valid_actions:
                value_Q = self.get_Q_value(state, action)
                if value_Q > max_Q:
                    max_Q = value_Q
                    best_action = action
                elif value_Q == max_Q:
                    if random.random() < 0.5:
                        best_action = action
        return (max_Q, best_action)

    def get_Q_value(self, state, action):
        """Get the value of Q given by the state and the action."""
        return self.value_Q.get((state, action), self.initial_Q)

def run():
    """Run the agent for a finite number of trials."""

    # Set up environment and agent
    e = Environment()  # create environment (also adds some dummy traffic)
    a = e.create_agent(LearningAgent)  # create agent
    e.set_primary_agent(a, enforce_deadline=True)  # specify agent to track
    # NOTE: You can set enforce_deadline=False while debugging to allow longer trials

    # Now simulate it
    sim = Simulator(e, update_delay=0, display=False)  # create simulator (uses pygame when display=True, if available)
    # NOTE: To speed up simulation, reduce update_delay and/or set display=False

    sim.run(n_trials=100)  # run for a specified number of trials
    # NOTE: To quit midway, press Esc or close pygame window, or hit Ctrl+C on the command-line

if __name__ == '__main__':
    run()