#import system module for command line arguments
import sys

# Global memory stack and procedures dictionary
memory_stack = [{}]  # Initialize with the global memory
procedures = {}


def main():
    # Get the number of command-line arguments
    argnum = len(sys.argv)

    # List of command-line arguments
    args = sys.argv

    # getting file name from the command line
    fileName = sys.argv[1]

    # reading in tokens from the file and storing them in a list
    potentialTokens = reader(fileName)

    # Passing tokens to the lexical analyzer
    tokens = lexicalAnalyzer(potentialTokens)

    # Validate tokens before passing to the parser
    if validate_tokens(tokens):
        # print("All tokens are valid. Proceeding to parser...")
        parser(tokens)
        # print("Main: Moving to execution...")
        execute(tokens)

        # Printing memory for debugging
        # print("Main: Final Memory:", memory_stack[0])

    else:
        print("Invalid tokens found in input")

def parser(tokens):
    # Split the 2d list into two separate lists
    tokenList = [token[1] for token in tokens]
    tokenTypeList = [token[0] for token in tokens]

    # Checking for program keyword in the beginning of the input
    if tokenList[0] != "program":
        print("Error: Input must begin with 'program' keyword")
        quit()
    # initializing the index
    index = 1

    # Check for program identifier
    if tokenTypeList[index] != "Identifier Token":
        print("Error: Program identifier missing")
        quit()
    index += 1

    # checking for semicolon
    if tokenList[index] != ";":
        print("Error: Missing Semicolon.")
        quit()
    index += 1

    # Calling block function to parse the body
    index = Block(tokenList, tokenTypeList, index)

    # Check for program-ending period
    if tokenList[index] != ".":
        print("Error: Missing period at end of program")
        quit()

    # print("Parser: Parsing completed")




# method that will execute the expressions
def execute(tokens):
    i = 0  # index for iterating over tokens

    while i < len(tokens):
        token_type, token_value = tokens[i]

        if token_value in ['if', 'read', 'write', 'begin', 'while'] or \
                (token_type == "Identifier Token" and i + 1 < len(tokens) and tokens[i + 1][1] == ":="):
            i = execute_statement(tokens, i)

        # Handling variable declarations
        elif token_value == "var":
            i = declare_variables(tokens, i + 1)
        elif token_value == "procedure":
            # Skip over procedure declarations during execution
            i = skip_procedure(tokens, i)
        else:
            i += 1


def current_memory():
    return memory_stack[-1]

def get_variable(var_name):
    # Search the memory stack from top to bottom
    for mem in reversed(memory_stack):
        if var_name in mem:
            return mem[var_name]
    return None


def skip_procedure(tokens, index):
    # skipping the "procedure" keyword and the name of the procedure
    index += 2

    if tokens[index][1] != ';':
        print("Error: Expected ';' after procedure declaration")
        return index
    index += 1 

    index = skip_block(tokens, index)

    # not expeciting an extra ";" after the body
    return index


def skip_block(tokens, index):
    while index < len(tokens):
        token_value = tokens[index][1]
        if token_value == 'var':
            #Skipping variable declarations
            index += 1
            while tokens[index][1] != ';':
                index += 1
            index += 1
        elif token_value == 'procedure':
            index = skip_procedure(tokens, index)
        elif token_value == 'begin':
            index = skip_statement(tokens, index)
            # returning after processing the block
            return index 
        else:

            break
    return index

def skip_statement(tokens, index):
    # Skips over a statement or block without executing
    if tokens[index][1] == 'begin':
        # Skips the compound statement
        index += 1
        while index < len(tokens) and tokens[index][1] != 'end':
            index = skip_statement(tokens, index)
        if index >= len(tokens):
            print("Error: Missing 'end' in compound statement")
            return index
        index += 1
        if index < len(tokens) and tokens[index][1] == ';':
            index += 1
    else:
        # Skip a simple statement
        while index < len(tokens) and tokens[index][1] != ';':
            index += 1
        if index < len(tokens) and tokens[index][1] == ';':
            index += 1
    return index



# Method for declaring variables
def declare_variables(tokens, i):
    current_mem = current_memory()
    while i < len(tokens):
        var_names = []
        # Parse variable names
        while tokens[i][0] == "Identifier Token":
            var_names.append(tokens[i][1])
            i += 1
            if tokens[i][1] == ",":
                # skip the comma
                i += 1
            else:
                break
        if tokens[i][1] != ":":
            print("Error: Expected ':' in variable declaration")
            break
        i += 1 
        if tokens[i][0] != "Data Type Token":
            print("Error: Data type expected in variable declaration")
            break
        var_type = tokens[i][1]
        # skips the datatype
        i += 1
        if tokens[i][1] != ";":
            print("Error: Expected ';' after variable declaration")
            break
        i += 1 
        #Declare variables
        for var_name in var_names:
            if var_type == "integer":
                current_mem[var_name] = {"type": var_type, "value": 0}
            else:
                print(f"Error: Unsupported type {var_type}")
        # check to see if the nxt token is an identifier token another declaration
        if i >= len(tokens) or tokens[i][0] != 'Identifier Token':
            break
    return i

def execute_statement(tokens, index):
    token_value = tokens[index][1]

    # handling variable declarations inside of procedures or blocks
    if token_value == 'var':
        index = declare_variables(tokens, index + 1)
        return index

    # Handle compound statements
    elif token_value == 'begin':
        index += 1 
        while index < len(tokens) and tokens[index][1] != 'end':
            index = execute_statement(tokens, index)
        if index >= len(tokens):
            print("Error: Missing 'end' in compound statement")
            return index
        index += 1
        if index < len(tokens) and tokens[index][1] == ';':
            index += 1
        return index

    # handles if statements with optional else block
    elif token_value == 'if':
        index += 1

        # extracting the condition
        condition_tokens = []
        while tokens[index][1] != 'then':
            condition_tokens.append(tokens[index])
            index += 1

        # evaluating the condition
        condition_result = evaluate_expression(condition_tokens)

        index += 1 

        if condition_result:
            # execute the statement
            index = execute_statement(tokens, index)
            # skip the else block if it exists
            if index < len(tokens) and tokens[index][1] == 'else':
                index += 1
                index = skip_statement(tokens, index)
        else:
            # skips the then block
            index = skip_statement(tokens, index)
            # execute the else block if it exists
            if index < len(tokens) and tokens[index][1] == 'else':
                index += 1
                index = execute_statement(tokens, index)
        # skip the semicolon after the if statement
        if index < len(tokens) and tokens[index][1] == ';':
            index += 1
        return index

    # while statements
    elif token_value == 'while':
        index += 1 

        # extracting the condition
        condition_tokens = []
        while tokens[index][1] != 'do':
            condition_tokens.append(tokens[index])
            index += 1

        index += 1

        # saving the index of the start of the loop body
        loopBodyStartPoint = index

        # using skip statement function to find the end of the loop body
        temp_index = index
        loop_body_end_index = skip_statement(tokens, temp_index)

        # execute the loop body while the condition is true
        while evaluate_expression(condition_tokens):
            loop_index = loopBodyStartPoint
            while loop_index < loop_body_end_index:
                loop_index = execute_statement(tokens, loop_index)
        # after the loop ends, move the index to after the loop body
        index = loop_body_end_index
        return index

    # handle write statements
    elif token_value == 'write':
        index += 1
        if tokens[index][1] != '(':
            print("Error: Expected '(' after 'write'")
            return index
        index += 1
        # collecting the expression tokens inside the parentheses
        expression_tokens = []
        while tokens[index][1] != ')':
            expression_tokens.append(tokens[index])
            index += 1
        # Evaluate the expression
        value = evaluate_expression(expression_tokens)
        print(value)
        index += 1 
        if index < len(tokens) and tokens[index][1] == ';':
            index += 1
        return index

    # handling read statement
    elif token_value == 'read':
        # skipping read
        index += 1 
        if tokens[index][1] != '(':
            print("Error: Expected '(' after 'read'")
            return index
        index += 1 
        var_name = tokens[index][1]
        var = get_variable(var_name)
        if var and var['type'] == 'integer':
            var['value'] = int(input(f"Enter value for {var_name}: "))
        else:
            print(f"Error: {var_name} is not declared or is not an integer.")
        # going past the variable name
        index += 1
        if tokens[index][1] != ')':
            print("Error: Expected ')' after variable name in 'read'")
            return index
        index += 1
        if index < len(tokens) and tokens[index][1] == ';':
            index += 1
        return index

    # handling assignment statement
    elif tokens[index][0] == "Identifier Token" and tokens[index + 1][1] == ":=":
        var_name = tokens[index][1]
        # skipping over variable name and the :=
        index += 2
        # collecting expression tokens until there is a semicolon or end of statement
        expression_tokens = []
        while index < len(tokens) and tokens[index][1] != ';':
            expression_tokens.append(tokens[index])
            index += 1
        # evaluate and assign
        expression_value = evaluate_expression(expression_tokens)
        var = get_variable(var_name)
        if var and var["type"] == 'integer':
            var['value'] = expression_value
        else:
            print(f"Error: {var_name} is not declared or is not an integer.")
        if index < len(tokens) and tokens[index][1] == ';':
            index += 1 
        return index

    # Handle the procedure calls
    elif tokens[index][0] == 'Identifier Token' and (index + 1 >= len(tokens) or tokens[index + 1][1] != ':='):
        proc_name = tokens[index][1]
        if proc_name in procedures:
            # this will push a new memory onto the stack
            memory_stack.append({})
            # execute the procedure body
            proc_tokens = procedures[proc_name]['tokens']
            proc_index = 0
            while proc_index < len(proc_tokens):
                proc_index = execute_statement(proc_tokens, proc_index)
            # Pop the memory stack after execution
            # popping the memory stack after execution
            memory_stack.pop()
            # move to the next token after the procedure call
            index += 1
            # skip semicolon if there is one
            if index < len(tokens) and tokens[index][1] == ';':
                index += 1
            return index
        else:
            print(f"Error: The procedure {proc_name} not defined.")
            index += 1
            return index

    # Handle unrecognized statements
    else:
        print(f"Error: Invalid statement starting with {token_value}.")
        index += 1
        return index

def evaluate_expression(tokens):
    # extract the expression tokens
    expression_tokens = []
    for token in tokens:
        if token[1] in [';', 'then', 'do']:
            break
        expression_tokens.append(token)

    # handle the comparison operators
    comparison_ops = ['=', '<>', '<', '<=', '>=', '>']
    for i, (token_type, token_value) in enumerate(expression_tokens):
        if token_value in comparison_ops:
            # Split expression into left and right parts
            left_tokens = expression_tokens[:i]
            right_tokens = expression_tokens[i + 1:]

            # Evaluate both sides
            left_value = evaluate_arithmetic(left_tokens)
            right_value = evaluate_arithmetic(right_tokens)

            # Compare based on operator
            if token_value == '=':
                return left_value == right_value
            elif token_value == '<>':
                return left_value != right_value
            elif token_value == '<':
                return left_value < right_value
            elif token_value == '<=':
                return left_value <= right_value
            elif token_value == '>=':
                return left_value >= right_value
            elif token_value == '>':
                return left_value > right_value

    # If there isn't a comparison operator, evaluate
    return evaluate_arithmetic(expression_tokens)



def evaluate_arithmetic(tokens):
    # build the expression string
    expression = ""
    for token_type, token_value in tokens:
        if token_type == "Integer Token":
            expression += token_value
        elif token_type == "Identifier Token":
            var = get_variable(token_value)
            if var and var["type"] == "integer":
                expression += str(var["value"])
            else:
                print(f"Error: {token_value} is not declared or is not an integer.")
                return 0
        elif token_value == "div":
            expression += " // "
        elif token_value in ["+", "-", "*", "/", "(", ")", "%"]:
            expression += f"{token_value}"
        elif token_value == " ":
            continue
        else:
            print(f"Error: Unrecognized token '{token_value}' in expression.")
            return 0

    try:
        result = eval(expression)
    except Exception as e:
        print(f"Error evaluating expression: {e}")
        return 0

    return result



# Parser block
def Block(stringList, tokenList, index):
    # parsing the variable declarations
    index = VarDeclarationPart(stringList, tokenList, index)
    index = ProcDeclarationPart(stringList, tokenList, index)
    index = StatementPart(stringList, tokenList, index)
    return index

def VarDeclarationPart(stringList, tokenList, index):
    # Skipping if there's no var declarations
    if stringList[index] != "var":
        return index

    index += 1
    while True:
        # Var identifiers
        if tokenList[index] != "Identifier Token":
            print("Identifier Expected")
            quit()

        index += 1
        # Checking for multiple identifiers when separated by commas
        while stringList[index] == ",":
            index += 1
            if tokenList[index] != "Identifier Token":
                print("Identifier Expected")
                quit()
            index += 1

        # Checking for the colon
        if stringList[index] != ":":
            print("Colon expected")
            quit()
        index += 1

        # Checking for the type
        if stringList[index] not in ["integer", "boolean"]:
            print("Variable type expected")
            quit()
        index += 1

        # checking for semicolon
        if stringList[index] != ";":
            print("Semicolon expected")
            quit()
        index += 1

        # checking if there are more variable declarations
        if tokenList[index] != "Identifier Token":
            break

    return index

def ProcDeclarationPart(stringList, tokenList, index):
    # reference to the global procedures dictionary
    global procedures

    while stringList[index] == "procedure":
        index += 1

        # name of the procedure
        if tokenList[index] != "Identifier Token":
            print("Procedure name expected")
            quit()
        procedureName = stringList[index]
        index += 1

        # semicolon after procedure name
        if stringList[index] != ";":
            print("Semicolon Expected")
            quit()
        index += 1

        # save the stating index of the procedure body
        procedureBodyStartIndex = index

        # process the procedure block
        index = Block(stringList, tokenList, index)

        # saving the ending index of the procedure body
        procedureBodyEndIndex = index

        # store the procedure in the dictionary and storing the token of the procedure body
        procedures[procedureName] = {
            'tokens': list(zip(tokenList[procedureBodyStartIndex:procedureBodyEndIndex], stringList[procedureBodyStartIndex:procedureBodyEndIndex]))
        }

        # ; after procedure block
        if stringList[index] != ";":
            index += 0 
        else:
            index += 1

    return index

def StatementPart(stringList, tokenList, index):
    # parse the compound statement
    return CompoundStatement(stringList, tokenList, index)

def CompoundStatement(stringList, tokenList, index):
    # checking for begin to start the compound statement
    if stringList[index] != "begin":
        print("Begin expected")
        quit()
    index += 1

    # processing each statement until the "end" is found
    while stringList[index] != "end":
        index = Statement(stringList, tokenList, index)

    # Move past "end" to complete the statement
    index += 1
    return index

def Statement(stringList, tokenList, index):
    # determining the type of statement
    if stringList[index] == "if":
        return IfStatement(stringList, tokenList, index)
    elif stringList[index] == "while":
        return WhileStatement(stringList, tokenList, index)
    elif stringList[index] == "begin":
        return CompoundStatement(stringList, tokenList, index)
    elif stringList[index] == "var":
        return VarDeclarationPart(stringList, tokenList, index)
    else:
        return SimpleStatement(stringList, tokenList, index)

def SimpleStatement(stringList, tokenList, index):
    # Check for read statement
    if stringList[index] == "read":
        index = ReadStatement(stringList, tokenList, index)

    # Check for write statement
    elif stringList[index] == "write":
        index = WriteStatement(stringList, tokenList, index)

    # checking for assignment or procedure statement
    elif tokenList[index] == "Identifier Token":
        if stringList[index + 1] == ":=":
            index = AssignmentStatement(stringList, tokenList, index)
        else:
            index = ProcedureStatement(stringList, tokenList, index)
    else:
        print("Invalid statement")
        quit()

    # Expecting a semicolon after the statement
    if stringList[index] != ";":
        print("Semicolon expected")
        quit()
    index += 1
    return index

def AssignmentStatement(stringList, tokenList, index):
    # skipping over variable name and assignment operator
    index += 2
    # Parsing the expression on the right-hand side
    index = Expression(stringList, tokenList, index)
    return index

def Expression(stringList, tokenList, index):
    # Parsing the simple expression on the left side
    index = SimpleExpression(stringList, tokenList, index)

    # Checking for relational operator for the comparisons
    if stringList[index] in ["=", "<>", "<", "<=", ">=", ">"]:
        index += 1
        index = SimpleExpression(stringList, tokenList, index)

    return index

def SimpleExpression(stringList, tokenList, index):
    # parse the first term
    index = Term(stringList, tokenList, index)

    # Checking for additional terms
    while stringList[index] in ["+", "-", "or"]:
        index += 1
        index = Term(stringList, tokenList, index)

    return index

def Term(stringList, tokenList, index):
    # parsing the first factor in the term
    index = Factor(stringList, tokenList, index)

    # Checking for multiplying operators
    while stringList[index] in ["*", "div", "and"]:
        index += 1
        index = Factor(stringList, tokenList, index)

    return index

def Factor(stringList, tokenList, index):
    # Parsing identifier as a factor
    if tokenList[index] == "Identifier Token":
        index += 1

    # Parsing integer constant
    elif tokenList[index] == "Integer Token":
        index += 1

    # parsing an expression in parentheses
    elif stringList[index] == "(":
        index += 1
        index = Expression(stringList, tokenList, index)
        if stringList[index] != ")":
            print("Error: Expected ')'")
            quit()
        index += 1

    # parsing the "not" followed by a factor
    elif stringList[index] == "not":
        index += 1
        index = Factor(stringList, tokenList, index)

    # For any invalid factor cases, quit
    else:
        print("Error: Invalid factor")
        quit()
    return index

def ReadStatement(stringList, tokenList, index):
    # skipping the "read" keyword
    index += 1

    if stringList[index] != "(":
        print("No opening parenthesis found")
        quit()
    index += 1

    if tokenList[index] != "Identifier Token":
        print("Variable expected in read statement")
        quit()
    index += 1

    if stringList[index] != ")":
        print("No closing parenthesis found")
        quit()
    index += 1
    return index

def WriteStatement(stringList, tokenList, index):
    # Skipping the write keyword
    index += 1

    if stringList[index] != "(":
        print("No opening parenthesis found")
        quit()
    index += 1

    # Parse the expression in the parentheses
    index = Expression(stringList, tokenList, index)

    if stringList[index] != ")":
        print("No closing parenthesis found")
        quit()

    index += 1
    return index

def IfStatement(stringList, tokenList, index):
    # Skipping the if keyword
    index += 1

    # parsing condition expression within the if statement
    index = Expression(stringList, tokenList, index)

    if stringList[index] != "then":
        print("There should be a then in the if statement")
        quit()
    index += 1

    # parsing the statement after the "then"
    index = Statement(stringList, tokenList, index)

    # handling the optional else statement
    if stringList[index] == "else":
        index += 1
        index = Statement(stringList, tokenList, index)

    return index

def WhileStatement(stringList, tokenList, index):
    # skipping the while keyword
    index += 1

    # parsing condition expression in the loop
    index = Expression(stringList, tokenList, index)

    # expecting a do to begin loop statement
    if stringList[index] != "do":
        print("There should be a do in the loop statement")
        quit()
    index += 1

    # parsing statement in the while loop
    index = Statement(stringList, tokenList, index)
    return index

def ProcedureStatement(stringList, tokenList, index):
    # ensure that there are no invalid tokens for the procedure call
    if tokenList[index] != "Identifier Token":
        print("Procedure call expected")
        quit()
    index += 1
    return index

def validate_tokens(token_list):
    # Loop going through and checking for invalid token type. Token value is ignored
    for token_type, token_value in token_list:
        if token_type == 'Invalid Token':
            return False
    return True

def lexicalAnalyzer(potentialTokens):
    # List to store tokens and their types
    tokens = []

    # Defining the grammar for the lexical analyzer
    reservedWords = {'program', 'var', 'procedure', 'begin', 'end', 'if', 'then', 'else', 'while', 'do', 'read',
                     'write'}
    dataTypes = {'integer', 'boolean'}
    booleanConstants = {'true', 'false'}
    assignmentOperator = {':='}
    relationalOperators = {'=', '<>', '<', '<=', '>=', '>'}
    addingOperators = {'+', '-', 'or'}
    multiplyingOperators = {'*', 'div', 'and'}
    specialSymbols = {'(', ')', '.', ',', ';', ':', '..', 'not'}
    letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p',
               'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
               'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P',
               'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

    # Looping through each token to categorize
    for token in potentialTokens:
        if token in reservedWords:
            tokens.append(('Reserved Token', token))
        elif token in dataTypes:
            tokens.append(('Data Type Token', token))
        elif token in booleanConstants:
            tokens.append(('Boolean Constant Token', token))
        elif token in assignmentOperator:
            tokens.append(('Assignment Token', token))
        elif token in relationalOperators:
            tokens.append(('Relational Token', token))
        elif token in addingOperators:
            tokens.append(('Addition Token', token))
        elif token in multiplyingOperators:
            tokens.append(('Multiplication Token', token))
        elif token in specialSymbols:
            tokens.append(('Special Token', token))
        # checking if token is an integer
        elif token.isdigit():
            tokens.append(('Integer Token', token))
        # Check if token is a valid identifier
        elif all(char in letters or char in digits for char in token):
            tokens.append(('Identifier Token', token))
        else:
            # Invalid Token
            tokens.append(('Invalid Token', token))

    # returning the list of tokens for further processing
    return tokens

def reader(filename):
    # Opening the file and reading the contents
    with open(filename, 'r') as file:
        content = file.read()

    # Splitting the contents by spaces
    potentialTokens = content.split()
    return potentialTokens

if __name__ == "__main__":
    main()