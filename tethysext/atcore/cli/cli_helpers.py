def print_error(statement):
    print('{}{}{}'.format('\033[91m', statement, '\033[0m'))


def print_success(statement):
    print('{}{}{}'.format('\033[92m', statement, '\033[0m'))


def print_warning(statement):
    print('{}{}{}'.format('\033[93m', statement, '\033[0m'))


def print_info(statement):
    print('{}{}{}'.format('\033[94m', statement, '\033[0m'))


def print_header(statement):
    print('{}{}{}'.format('\033[95m', statement, '\033[0m'))
