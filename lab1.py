from flask import Flask, render_template, request
import graphviz
import re
from collections import defaultdict

app = Flask(__name__)

# Implementación del algoritmo de Shunting Yard
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

# Construcción del AFN
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

# Construcción del árbol de sintaxis
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

# Visualización del AF usando Graphviz
def visualize_automaton(automaton, filename):
    dot = graphviz.Digraph(format='png')
    for state in automaton['transitions']:
        shape = 'doublecircle' if state in automaton['final'] else 'circle'
        dot.node(str(state), shape=shape)
    
    for state, trans_dict in automaton['transitions'].items():
        for symbol, next_states in trans_dict.items():
            for next_state in next_states:
                dot.edge(str(state), str(next_state), label=symbol if symbol else 'ε')
    
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
        construct_syntax_tree(postfix)
        visualize_automaton(afn, 'static/afn')
        result = f"Postfix: {postfix}"
        afn_path = 'static/afn.png'
        tree_path = 'static/syntax_tree.png'
    return render_template('index.html', result=result, afn_path=afn_path, tree_path=tree_path)

if __name__ == '__main__':
    app.run(debug=True)
