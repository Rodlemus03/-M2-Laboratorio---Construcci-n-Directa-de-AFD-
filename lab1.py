from flask import Flask, render_template, request
import graphviz
from collections import defaultdict
import os

app = Flask(__name__)

# Shutting yard

def infix_to_postfix(expression):
    precedence = {'|': 1, '.': 2, '*': 3}
    output = []
    stack = []
    
    for char in expression:
        if char.isalnum():
            output.append(char)
        elif char == '(':
            stack.append(char)
        elif char == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            stack.pop()
        else:
            while stack and stack[-1] != '(' and precedence[stack[-1]] >= precedence[char]:
                output.append(stack.pop())
            stack.append(char)
    
    while stack:
        output.append(stack.pop())
    
    return ''.join(output)

class Node:
    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right
        self.nullable = False
        self.firstpos = set()
        self.lastpos = set()
        self.position = None

def postfix_to_tree(postfix):
    stack = []
    position = 1
    for symbol in postfix:
        if symbol.isalnum():
            node = Node(symbol)
            node.position = position
            node.firstpos.add(position)
            node.lastpos.add(position)
            position += 1
            stack.append(node)
        elif symbol in "|.*":
            if symbol == "*":
                child = stack.pop()
                node = Node(symbol, left=child)
            else:
                right = stack.pop()
                left = stack.pop()
                node = Node(symbol, left, right)
            stack.append(node)
    return stack.pop()

def compute_nullable_first_last(node):
    if node is None:
        return
    compute_nullable_first_last(node.left)
    compute_nullable_first_last(node.right)
    
    if node.value.isalnum():
        node.nullable = False
    elif node.value == "*":
        node.nullable = True
        node.firstpos = node.left.firstpos
        node.lastpos = node.left.lastpos
    elif node.value == "|":
        node.nullable = node.left.nullable or node.right.nullable
        node.firstpos = node.left.firstpos | node.right.firstpos
        node.lastpos = node.left.lastpos | node.right.lastpos
    elif node.value == ".":
        node.nullable = node.left.nullable and node.right.nullable
        node.firstpos = node.left.firstpos if not node.left.nullable else node.left.firstpos | node.right.firstpos
        node.lastpos = node.right.lastpos if not node.right.nullable else node.left.lastpos | node.right.lastpos

def compute_followpos(node, followpos_table):
    if node is None:
        return
    compute_followpos(node.left, followpos_table)
    compute_followpos(node.right, followpos_table)
    if node.value == ".":
        for pos in node.left.lastpos:
            followpos_table[pos] |= node.right.firstpos
    elif node.value == "*":
        for pos in node.lastpos:
            followpos_table[pos] |= node.firstpos

def build_afd(infix_expression):
    postfix = infix_to_postfix(infix_expression)
    tree = postfix_to_tree(postfix)
    compute_nullable_first_last(tree)
    followpos_table = defaultdict(set)
    compute_followpos(tree, followpos_table)
    return postfix, tree, followpos_table

def visualize_tree(tree):
    dot = graphviz.Digraph(format='png')
    def add_nodes_edges(node):
        if node:
            dot.node(str(id(node)), node.value)
            if node.left:
                dot.edge(str(id(node)), str(id(node.left)))
                add_nodes_edges(node.left)
            if node.right:
                dot.edge(str(id(node)), str(id(node.right)))
                add_nodes_edges(node.right)
    add_nodes_edges(tree)
    image_path = "static/syntax_tree.png"
    dot.render(image_path[:-4])
    return image_path

@app.route('/', methods=['GET', 'POST'])
def index():
    image_path = None
    postfix = ""
    followpos_table = {}
    if request.method == 'POST':
        infix_expression = request.form['expression']
        postfix, tree, followpos_table = build_afd(infix_expression)
        image_path = visualize_tree(tree)
    return render_template('index.html', image_path=image_path, postfix=postfix, followpos_table=followpos_table)

if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    app.run(debug=True)
