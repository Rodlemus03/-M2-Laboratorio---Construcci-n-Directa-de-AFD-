from flask import Flask, render_template, request
import graphviz
import re
from collections import defaultdict

app = Flask(__name__)

def infix_to_postfix(expression):
    precedence = {'|': 1, '.': 2, '*': 3, '+': 3, '?': 3}
    output = []
    stack = []
    
    for char in expression:
        if char.isalnum():
            output.append(char)
        elif char in precedence:
            while stack and precedence.get(stack[-1], 0) >= precedence[char]:
                output.append(stack.pop())
            stack.append(char)
        elif char == '(':
            stack.append(char)
        elif char == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            stack.pop()
    
    while stack:
        output.append(stack.pop())
    
    return ''.join(output)

def construct_afn(postfix):
    state_count = 0
    stack = []
    transitions = {}
    
    for symbol in postfix:
        if symbol.isalnum():
            start, end = state_count, state_count + 1
            transitions.setdefault(start, {}).setdefault(symbol, set()).add(end)
            stack.append((start, end))
            state_count += 2
        elif symbol in {'|', '.', '*'}:
            if symbol == '|':
                s1_start, s1_end = stack.pop()
                s2_start, s2_end = stack.pop()
                new_start, new_end = state_count, state_count + 1
                transitions.setdefault(new_start, {}).setdefault('', set()).update({s1_start, s2_start})
                transitions.setdefault(s1_end, {}).setdefault('', set()).add(new_end)
                transitions.setdefault(s2_end, {}).setdefault('', set()).add(new_end)
                stack.append((new_start, new_end))
                state_count += 2
            elif symbol == '.':
                s2_start, s2_end = stack.pop()
                s1_start, s1_end = stack.pop()
                transitions.setdefault(s1_end, {}).setdefault('', set()).add(s2_start)
                stack.append((s1_start, s2_end))
            elif symbol == '*':
                s_start, s_end = stack.pop()
                new_start, new_end = state_count, state_count + 1
                transitions.setdefault(new_start, {}).setdefault('', set()).update({s_start, new_end})
                transitions.setdefault(s_end, {}).setdefault('', set()).update({s_start, new_end})
                stack.append((new_start, new_end))
                state_count += 2
    
    start_state, final_state = stack.pop()
    return {'start': start_state, 'final': {final_state}, 'transitions': transitions}

def construct_afd(afn):
    dfa_transitions = {}
    states = {frozenset([afn['start']]): 0}
    queue = [frozenset([afn['start']])]
    state_count = 1
    final_states = set()
    
    while queue:
        current_set = queue.pop()
        state_id = states[current_set]
        symbol_map = defaultdict(set)
        
        for state in current_set:
            for symbol, to_states in afn['transitions'].get(state, {}).items():
                symbol_map[symbol].update(to_states)
        
        for symbol, to_set in symbol_map.items():
            to_set = frozenset(to_set)
            if to_set not in states:
                states[to_set] = state_count
                queue.append(to_set)
                state_count += 1
            dfa_transitions.setdefault(state_id, {})[symbol] = states[to_set]
            
            if to_set & afn['final']:
                final_states.add(states[to_set])
    
    return {'start': 0, 'final': final_states, 'transitions': dfa_transitions}

def construct_syntax_tree(postfix):
    tree = graphviz.Digraph(format='png')
    node_count = 0
    stack = []
    
    for symbol in postfix:
        node_name = f"n{node_count}"
        tree.node(node_name, label=symbol)
        node_count += 1
        
        if symbol.isalnum():
            stack.append(node_name)
        else:
            if symbol in {'|', '.', '*'}:
                if symbol == '*':
                    child = stack.pop()
                    tree.edge(node_name, child)
                else:
                    right = stack.pop()
                    left = stack.pop()
                    tree.edge(node_name, left)
                    tree.edge(node_name, right)
                
            stack.append(node_name)
    
    tree.render('static/syntax_tree', format='png', cleanup=True)

def visualize_automaton(automaton, filename):
    dot = graphviz.Digraph(format='png')
    for state in automaton['transitions']:
        shape = 'doublecircle' if state in automaton['final'] else 'circle'
        dot.node(str(state), shape=shape)
    
    for state, trans_dict in automaton['transitions'].items():
        for symbol, next_states in trans_dict.items():
            dot.edge(str(state), str(next_states), label=symbol if symbol else 'ε')
    
    dot.render(filename, cleanup=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    afn_path = None
    afd_path = None
    tree_path = None
    if request.method == 'POST':
        expression = request.form['expression']
        postfix = infix_to_postfix(expression)
        afn = construct_afn(postfix)
        afd = construct_afd(afn)
        construct_syntax_tree(postfix)
        visualize_automaton(afn, 'static/afn')
        visualize_automaton(afd, 'static/afd')
        result = f"Postfix: {postfix}"
        afn_path = 'static/afn.png'
        afd_path = 'static/afd.png'
        tree_path = 'static/syntax_tree.png'
    return render_template('index.html', result=result, afn_path=afn_path, afd_path=afd_path, tree_path=tree_path)

if __name__ == '__main__':
    app.run(debug=True)
