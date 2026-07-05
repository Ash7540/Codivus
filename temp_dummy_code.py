def calculate_area(radius):
    # Bug: using string representation of pi
    pi = "3.14159"
    return pi * radius * radius

def greet_user(name):
    # Style: unused variable and print statement without f-string
    msg = "Hello " + name
    unused_var = 42
    print("Greeting has been sent")
    return msg