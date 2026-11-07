import os
from datetime import datetime, timedelta
import subprocess
import tempfile
import textwrap
import sqlite3

# =========================================================
# COURSE ENROLLMENT DATABASE
# =========================================================

COURSE_DB = "careerai_courses.db"


def init_course_database():
    connection = sqlite3.connect(COURSE_DB)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            course_id TEXT NOT NULL,
            enrolled_at TEXT NOT NULL,
            UNIQUE(user_email, course_id)
        )
    """)

    connection.commit()
    connection.close()



    # =========================================================
# COURSE ENROLLMENT HELPER FUNCTIONS
# =========================================================

def save_enrollment(user_email, course_id):

    connection = sqlite3.connect(COURSE_DB)

    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO enrollments
        (user_email, course_id, enrolled_at)
        VALUES (?, ?, ?)
    """, (
        user_email,
        course_id,
        datetime.now().isoformat()
    ))

    connection.commit()

    connection.close()


def get_enrolled_course_ids(user_email):

    connection = sqlite3.connect(COURSE_DB)

    cursor = connection.cursor()

    cursor.execute("""
        SELECT course_id
        FROM enrollments
        WHERE user_email = ?
        ORDER BY enrolled_at ASC
    """, (user_email,))

    course_ids = [row[0] for row in cursor.fetchall()]

    connection.close()

    return course_ids


def init_progress_database():
    """Create persistent storage for completed course lessons."""
    connection = sqlite3.connect(COURSE_DB)
    try:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS course_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                course_id TEXT NOT NULL,
                lesson_id TEXT NOT NULL,
                completed_at TEXT NOT NULL,
                UNIQUE(user_email, course_id, lesson_id)
            )
        """)
        connection.commit()
    finally:
        connection.close()


def save_completed_lesson(user_email, course_id, lesson_id):
    connection = sqlite3.connect(COURSE_DB)
    try:
        connection.execute("""
            INSERT OR IGNORE INTO course_progress
                (user_email, course_id, lesson_id, completed_at)
            VALUES (?, ?, ?, ?)
        """, (user_email, course_id, lesson_id, datetime.now().isoformat()))
        connection.commit()
    finally:
        connection.close()


def get_completed_lessons(user_email, course_id):
    connection = sqlite3.connect(COURSE_DB)
    try:
        rows = connection.execute("""
            SELECT lesson_id FROM course_progress
            WHERE user_email = ? AND course_id = ?
            ORDER BY id ASC
        """, (user_email, course_id)).fetchall()
        return [row[0] for row in rows]
    finally:
        connection.close()

    

from flask import Flask, render_template, request, redirect, url_for, session, flash

from database.skill_requirements import SKILL_REQUIREMENTS
from database.courses import (
    get_all_courses,
    get_course_by_id,
    get_courses_by_skill,
    get_courses_by_role,
    get_free_courses,
    get_paid_courses,
)
from database.course_lessons import (
    get_course_lessons,
    get_lesson,
    get_total_lessons,
)
from ai.skill_analyzer import analyze_skills
from ai.resume_analyzer import analyze_resume


app = Flask(__name__)

# =========================================================
# FLASK SESSION
# =========================================================

app.secret_key = "careerai-secret-key"


# =========================================================
# ASSESSMENT CONFIGURATION
# =========================================================

ASSESSMENT_TOTAL_QUESTIONS = 64
ASSESSMENT_DURATION_MINUTES = 125


# =========================================================
# ASSESSMENT QUESTION BANK
# =========================================================
#
# 64 QUESTIONS
#
# 7 SECTIONS
#
# 1. Quantitative Aptitude      - 10
# 2. Logical Reasoning          - 10
# 3. Python                     - 10
# 4. OOP                       - 8
# 5. Data Structures & Algo     - 10
# 6. SQL & DBMS                 - 8
# 7. Web/API/Git                - 8
#
# TOTAL = 64
# =========================================================

ASSESSMENT_QUESTIONS = [

    # =====================================================
    # SECTION 1 - QUANTITATIVE APTITUDE
    # 10 QUESTIONS
    # =====================================================

    {
        "section": "Quantitative Aptitude",
        "question": "If a number is increased by 20%, it becomes 240. What was the original number?",
        "options": [
            "180",
            "200",
            "220",
            "240"
        ],
        "answer": "200",
        "skill": "Quantitative Aptitude"
    },

    {
        "section": "Quantitative Aptitude",
        "question": "What is 25% of 360?",
        "options": [
            "60",
            "80",
            "90",
            "100"
        ],
        "answer": "90",
        "skill": "Quantitative Aptitude"
    },

    {
        "section": "Quantitative Aptitude",
        "question": "A train travels 120 km in 2 hours. What is its average speed?",
        "options": [
            "40 km/h",
            "50 km/h",
            "60 km/h",
            "80 km/h"
        ],
        "answer": "60 km/h",
        "skill": "Quantitative Aptitude"
    },

    {
        "section": "Quantitative Aptitude",
        "question": "What is the average of 10, 20, 30, 40 and 50?",
        "options": [
            "25",
            "30",
            "35",
            "40"
        ],
        "answer": "30",
        "skill": "Quantitative Aptitude"
    },

    {
        "section": "Quantitative Aptitude",
        "question": "If the ratio of A:B is 2:3 and A is 20, what is B?",
        "options": [
            "25",
            "30",
            "35",
            "40"
        ],
        "answer": "30",
        "skill": "Quantitative Aptitude"
    },

    {
        "section": "Quantitative Aptitude",
        "question": "A product costs ₹800 and is sold for ₹1,000. What is the profit percentage?",
        "options": [
            "20%",
            "25%",
            "30%",
            "15%"
        ],
        "answer": "25%",
        "skill": "Quantitative Aptitude"
    },

    {
        "section": "Quantitative Aptitude",
        "question": "What is the simple interest on ₹5,000 at 10% per year for 2 years?",
        "options": [
            "₹500",
            "₹750",
            "₹1,000",
            "₹1,500"
        ],
        "answer": "₹1,000",
        "skill": "Quantitative Aptitude"
    },

    {
        "section": "Quantitative Aptitude",
        "question": "If 5 workers complete a task in 12 days, how many days will 10 workers take, assuming equal efficiency?",
        "options": [
            "3",
            "5",
            "6",
            "8"
        ],
        "answer": "6",
        "skill": "Quantitative Aptitude"
    },

    {
        "section": "Quantitative Aptitude",
        "question": "What is the next number in the sequence 2, 4, 8, 16, ?",
        "options": [
            "20",
            "24",
            "30",
            "32"
        ],
        "answer": "32",
        "skill": "Quantitative Aptitude"
    },

    {
        "section": "Quantitative Aptitude",
        "question": "If x + 15 = 40, what is x?",
        "options": [
            "15",
            "20",
            "25",
            "30"
        ],
        "answer": "25",
        "skill": "Quantitative Aptitude"
    },


    # =====================================================
    # SECTION 2 - LOGICAL REASONING
    # 10 QUESTIONS
    # =====================================================

    {
        "section": "Logical Reasoning",
        "question": "Find the next number: 3, 6, 12, 24, ?",
        "options": [
            "36",
            "42",
            "48",
            "54"
        ],
        "answer": "48",
        "skill": "Logical Reasoning"
    },

    {
        "section": "Logical Reasoning",
        "question": "If all roses are flowers and some flowers fade quickly, which statement is definitely true?",
        "options": [
            "All roses fade quickly",
            "Some roses are not flowers",
            "Roses are flowers",
            "No flowers are roses"
        ],
        "answer": "Roses are flowers",
        "skill": "Logical Reasoning"
    },

    {
        "section": "Logical Reasoning",
        "question": "Which number does not belong to the group?",
        "options": [
            "2",
            "4",
            "8",
            "15"
        ],
        "answer": "15",
        "skill": "Logical Reasoning"
    },

    {
        "section": "Logical Reasoning",
        "question": "If CAT is coded as DBU, how is DOG coded?",
        "options": [
            "EPH",
            "EOH",
            "DPG",
            "FPH"
        ],
        "answer": "EPH",
        "skill": "Logical Reasoning"
    },

    {
        "section": "Logical Reasoning",
        "question": "A is taller than B. B is taller than C. Who is the shortest?",
        "options": [
            "A",
            "B",
            "C",
            "Cannot determine"
        ],
        "answer": "C",
        "skill": "Logical Reasoning"
    },

    {
        "section": "Logical Reasoning",
        "question": "Find the odd one out.",
        "options": [
            "Apple",
            "Mango",
            "Carrot",
            "Banana"
        ],
        "answer": "Carrot",
        "skill": "Logical Reasoning"
    },

    {
        "section": "Logical Reasoning",
        "question": "If today is Monday, what day will it be after 10 days?",
        "options": [
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday"
        ],
        "answer": "Thursday",
        "skill": "Logical Reasoning"
    },

    {
        "section": "Logical Reasoning",
        "question": "Which word is most closely related to 'keyboard'?",
        "options": [
            "Input",
            "Printer",
            "Monitor",
            "Speaker"
        ],
        "answer": "Input",
        "skill": "Logical Reasoning"
    },

    {
        "section": "Logical Reasoning",
        "question": "Complete the pattern: A, C, E, G, ?",
        "options": [
            "H",
            "I",
            "J",
            "K"
        ],
        "answer": "I",
        "skill": "Logical Reasoning"
    },

    {
        "section": "Logical Reasoning",
        "question": "If 1 = 3, 2 = 6, 3 = 9, then 7 = ?",
        "options": [
            "14",
            "18",
            "21",
            "24"
        ],
        "answer": "21",
        "skill": "Logical Reasoning"
    },


    # =====================================================
    # SECTION 3 - PYTHON
    # 10 QUESTIONS
    # =====================================================

    {
        "section": "Python",
        "type": "coding",
        "question": "Write a Python function reverse_string(s) that returns the reverse of a string.",
        "skill": "Python",
        "language": "Python",
        "starter_code": "def reverse_string(s):\n    # Write your code here\n    pass",
        "test_code": "print(reverse_string('hello'))\nprint(reverse_string('CareerAI'))",
        "expected_output": "olleh\nIAreeraC"
    },

    {
        "section": "Python",
        "type": "coding",
        "question": "Write a Python function is_palindrome(s) that returns True if the string is a palindrome, otherwise False.",
        "skill": "Python",
        "language": "Python",
        "starter_code": "def is_palindrome(s):\n    # Write your code here\n    pass",
        "test_code": "print(is_palindrome('madam'))\nprint(is_palindrome('python'))",
        "expected_output": "True\nFalse"
    },

    {
        "section": "Python",
        "type": "coding",
        "question": "Write a Python function count_vowels(s) that returns the number of vowels in a string.",
        "skill": "Python",
        "language": "Python",
        "starter_code": "def count_vowels(s):\n    # Write your code here\n    pass",
        "test_code": "print(count_vowels('hello'))\nprint(count_vowels('education'))",
        "expected_output": "2\n5"
    },

    {
        "section": "Python",
        "type": "coding",
        "question": "Write a Python function second_largest(nums) that returns the second largest distinct number in a list.",
        "skill": "Python",
        "language": "Python",
        "starter_code": "def second_largest(nums):\n    # Write your code here\n    pass",
        "test_code": "print(second_largest([10, 5, 8, 20, 15]))\nprint(second_largest([4, 4, 2, 3]))",
        "expected_output": "15\n3"
    },

    {
        "section": "Python",
        "question": "Which function is used to find the length of a list?",
        "options": [
            "size()",
            "length()",
            "len()",
            "count()"
        ],
        "answer": "len()",
        "skill": "Python"
    },

    {
        "section": "Python",
        "question": "Which keyword is used to handle exceptions?",
        "options": [
            "try",
            "catch",
            "handle",
            "exception"
        ],
        "answer": "try",
        "skill": "Python"
    },

    {
        "section": "Python",
        "question": "Which data structure stores key-value pairs?",
        "options": [
            "List",
            "Tuple",
            "Dictionary",
            "Set"
        ],
        "answer": "Dictionary",
        "skill": "Python"
    },

    {
        "section": "Python",
        "question": "What does OOP stand for?",
        "options": [
            "Object Oriented Programming",
            "Object Operating Program",
            "Open Object Programming",
            "Organized Object Process"
        ],
        "answer": "Object Oriented Programming",
        "skill": "Python"
    },

    {
        "section": "Python",
        "question": "Which operator is used for exponentiation in Python?",
        "options": [
            "^",
            "**",
            "//",
            "%%"
        ],
        "answer": "**",
        "skill": "Python"
    },

    {
        "section": "Python",
        "question": "Which keyword is used to create a class in Python?",
        "options": [
            "object",
            "class",
            "struct",
            "define"
        ],
        "answer": "class",
        "skill": "Python"
    },


    # =====================================================
    # SECTION 4 - OOP
    # 8 QUESTIONS
    # =====================================================

    {
        "section": "OOP",
        "question": "Which OOP concept allows a class to inherit properties from another class?",
        "options": [
            "Encapsulation",
            "Inheritance",
            "Abstraction",
            "Polymorphism"
        ],
        "answer": "Inheritance",
        "skill": "OOP"
    },

    {
        "section": "OOP",
        "question": "Which OOP concept hides internal implementation details?",
        "options": [
            "Inheritance",
            "Polymorphism",
            "Abstraction",
            "Overloading"
        ],
        "answer": "Abstraction",
        "skill": "OOP"
    },

    {
        "section": "OOP",
        "question": "Which concept combines data and methods into a single unit?",
        "options": [
            "Encapsulation",
            "Inheritance",
            "Compilation",
            "Recursion"
        ],
        "answer": "Encapsulation",
        "skill": "OOP"
    },

    {
        "section": "OOP",
        "question": "Polymorphism means:",
        "options": [
            "One class only",
            "Many forms",
            "Data hiding",
            "Code deletion"
        ],
        "answer": "Many forms",
        "skill": "OOP"
    },

    {
        "section": "OOP",
        "type": "coding",
        "question": "Create a Python class Rectangle with __init__(length, width) and an area() method that returns length * width.",
        "skill": "OOP",
        "language": "Python",
        "starter_code": "class Rectangle:\n    def __init__(self, length, width):\n        # Write your code here\n        pass\n\n    def area(self):\n        # Write your code here\n        pass",
        "test_code": "r = Rectangle(5, 4)\nprint(r.area())\nr = Rectangle(10, 3)\nprint(r.area())",
        "expected_output": "20\n30"
    },

    {
        "section": "OOP",
        "question": "Which relationship represents an 'is-a' relationship?",
        "options": [
            "Inheritance",
            "Aggregation",
            "Composition",
            "Association"
        ],
        "answer": "Inheritance",
        "skill": "OOP"
    },

    {
        "section": "OOP",
        "question": "Method overloading means:",
        "options": [
            "Same method name with different parameters",
            "Deleting a method",
            "Using only one method",
            "Creating multiple classes"
        ],
        "answer": "Same method name with different parameters",
        "skill": "OOP"
    },

    {
        "section": "OOP",
        "question": "Which access level generally restricts direct access to class data?",
        "options": [
            "Private",
            "Public",
            "Global",
            "Static"
        ],
        "answer": "Private",
        "skill": "OOP"
    },


    # =====================================================
    # SECTION 5 - DATA STRUCTURES & ALGORITHMS
    # 10 QUESTIONS
    # =====================================================

    {
        "section": "Data Structures & Algorithms",
        "question": "Which data structure follows the LIFO principle?",
        "options": [
            "Queue",
            "Stack",
            "Array",
            "Linked List"
        ],
        "answer": "Stack",
        "skill": "Data Structures"
    },

    {
        "section": "Data Structures & Algorithms",
        "question": "Which data structure follows the FIFO principle?",
        "options": [
            "Stack",
            "Queue",
            "Tree",
            "Graph"
        ],
        "answer": "Queue",
        "skill": "Data Structures"
    },

    {
        "section": "Data Structures & Algorithms",
        "question": "What is the average time complexity of binary search?",
        "options": [
            "O(n)",
            "O(n²)",
            "O(log n)",
            "O(1)"
        ],
        "answer": "O(log n)",
        "skill": "Algorithms"
    },

    {
        "section": "Data Structures & Algorithms",
        "question": "Which data structure is commonly used to implement a priority queue?",
        "options": [
            "Heap",
            "Stack",
            "Array only",
            "Linked list only"
        ],
        "answer": "Heap",
        "skill": "Data Structures"
    },

    {
        "section": "Data Structures & Algorithms",
        "question": "Which traversal visits the root before its subtrees?",
        "options": [
            "Inorder",
            "Postorder",
            "Preorder",
            "Level order"
        ],
        "answer": "Preorder",
        "skill": "Algorithms"
    },

    {
        "section": "Data Structures & Algorithms",
        "type": "coding",
        "question": "Write a Python function linear_search(nums, target) that returns the index of target, or -1 if it is not present.",
        "skill": "Algorithms",
        "language": "Python",
        "starter_code": "def linear_search(nums, target):\n    # Write your code here\n    pass",
        "test_code": "print(linear_search([4, 7, 1, 9], 1))\nprint(linear_search([4, 7, 1, 9], 5))",
        "expected_output": "2\n-1"
    },

    {
        "section": "Data Structures & Algorithms",
        "type": "coding",
        "question": "Write a Python function find_max(nums) that returns the maximum value in a non-empty list without using max().",
        "skill": "Data Structures",
        "language": "Python",
        "starter_code": "def find_max(nums):\n    # Write your code here\n    pass",
        "test_code": "print(find_max([3, 8, 2, 10, 5]))\nprint(find_max([-5, -2, -9]))",
        "expected_output": "10\n-2"
    },

    {
        "section": "Data Structures & Algorithms",
        "question": "Which algorithm is commonly used to find the shortest path in a weighted graph with non-negative edges?",
        "options": [
            "Bubble Sort",
            "Dijkstra's Algorithm",
            "Binary Search",
            "Linear Search"
        ],
        "answer": "Dijkstra's Algorithm",
        "skill": "Algorithms"
    },

    {
        "section": "Data Structures & Algorithms",
        "question": "Which sorting algorithm repeatedly swaps adjacent elements when they are in the wrong order?",
        "options": [
            "Merge Sort",
            "Quick Sort",
            "Bubble Sort",
            "Heap Sort"
        ],
        "answer": "Bubble Sort",
        "skill": "Algorithms"
    },

    {
        "section": "Data Structures & Algorithms",
        "question": "What is the typical time complexity of merge sort?",
        "options": [
            "O(n)",
            "O(log n)",
            "O(n log n)",
            "O(n²)"
        ],
        "answer": "O(n log n)",
        "skill": "Algorithms"
    },


    # =====================================================
    # SECTION 6 - SQL & DBMS
    # 8 QUESTIONS
    # =====================================================

    {
        "section": "SQL & DBMS",
        "type": "sql",
        "question": "Write a SQL query to display the names of employees whose salary is greater than 50000, ordered by salary from highest to lowest.",
        "skill": "SQL",
        "language": "SQL",
        "starter_code": "-- Write your SQL query here\n",
        "sql_schema": "CREATE TABLE employees (id INTEGER, name TEXT, department TEXT, salary INTEGER); INSERT INTO employees VALUES (1, 'Alice', 'IT', 60000), (2, 'Bob', 'HR', 45000), (3, 'Charlie', 'IT', 75000), (4, 'David', 'Sales', 50000);",
        "expected_output": "Charlie\nAlice"
    },

    {
        "section": "SQL & DBMS",
        "question": "Which SQL clause is used to filter rows?",
        "options": [
            "ORDER BY",
            "GROUP BY",
            "WHERE",
            "SORT"
        ],
        "answer": "WHERE",
        "skill": "SQL"
    },

    {
        "section": "SQL & DBMS",
        "question": "Which key uniquely identifies a record in a table?",
        "options": [
            "Foreign Key",
            "Primary Key",
            "Candidate Key",
            "Alternate Key"
        ],
        "answer": "Primary Key",
        "skill": "DBMS"
    },

    {
        "section": "SQL & DBMS",
        "question": "Which SQL command is used to add a new row?",
        "options": [
            "ADD",
            "INSERT",
            "UPDATE",
            "CREATE"
        ],
        "answer": "INSERT",
        "skill": "SQL"
    },

    {
        "section": "SQL & DBMS",
        "type": "sql",
        "question": "Write a SQL query to find the average salary of employees in the IT department.",
        "skill": "SQL",
        "language": "SQL",
        "starter_code": "-- Write your SQL query here\n",
        "sql_schema": "CREATE TABLE employees (id INTEGER, name TEXT, department TEXT, salary INTEGER); INSERT INTO employees VALUES (1, 'Alice', 'IT', 60000), (2, 'Bob', 'HR', 45000), (3, 'Charlie', 'IT', 75000), (4, 'David', 'Sales', 50000);",
        "expected_output": "67500.0"
    },

    {
        "section": "SQL & DBMS",
        "type": "sql",
        "question": "Write a SQL query to display each employee name together with the department name using the employees and departments tables.",
        "skill": "SQL",
        "language": "SQL",
        "starter_code": "-- Write your SQL query here\n",
        "sql_schema": "CREATE TABLE departments (id INTEGER, department_name TEXT); CREATE TABLE employees (id INTEGER, name TEXT, department_id INTEGER); INSERT INTO departments VALUES (1, 'IT'), (2, 'HR'); INSERT INTO employees VALUES (1, 'Alice', 1), (2, 'Bob', 2), (3, 'Charlie', 1);",
        "expected_output": "Alice|IT\nBob|HR\nCharlie|IT"
    },

    {
        "section": "SQL & DBMS",
        "question": "What is normalization mainly used for?",
        "options": [
            "Increasing duplicate data",
            "Reducing redundancy",
            "Deleting databases",
            "Increasing storage"
        ],
        "answer": "Reducing redundancy",
        "skill": "DBMS"
    },

    {
        "section": "SQL & DBMS",
        "question": "Which database is a NoSQL database?",
        "options": [
            "MySQL",
            "MongoDB",
            "Oracle",
            "SQLite"
        ],
        "answer": "MongoDB",
        "skill": "DBMS"
    },


    # =====================================================
    # SECTION 7 - WEB / API / GIT
    # 8 QUESTIONS
    # =====================================================

    {
        "section": "Web/API/Git",
        "question": "Which HTML tag is used to create a hyperlink?",
        "options": [
            "<link>",
            "<a>",
            "<href>",
            "<url>"
        ],
        "answer": "<a>",
        "skill": "HTML"
    },

    {
        "section": "Web/API/Git",
        "question": "Which CSS property is used to change text color?",
        "options": [
            "font-color",
            "text-color",
            "color",
            "foreground"
        ],
        "answer": "color",
        "skill": "CSS"
    },

    {
        "section": "Web/API/Git",
        "question": "Which keyword declares a block-scoped variable in JavaScript?",
        "options": [
            "var",
            "let",
            "define",
            "variable"
        ],
        "answer": "let",
        "skill": "JavaScript"
    },

    {
        "section": "Web/API/Git",
        "question": "What does REST API commonly use for data exchange?",
        "options": [
            "JSON",
            "MP3",
            "EXE",
            "PNG"
        ],
        "answer": "JSON",
        "skill": "REST API"
    },

    {
        "section": "Web/API/Git",
        "question": "Which HTTP method is normally used to retrieve data?",
        "options": [
            "POST",
            "GET",
            "DELETE",
            "PATCH"
        ],
        "answer": "GET",
        "skill": "REST API"
    },

    {
        "section": "Web/API/Git",
        "question": "Which command creates a new Git repository?",
        "options": [
            "git create",
            "git new",
            "git init",
            "git start"
        ],
        "answer": "git init",
        "skill": "Git"
    },

    {
        "section": "Web/API/Git",
        "question": "GitHub is mainly used for:",
        "options": [
            "Video editing",
            "Code hosting and collaboration",
            "Database management",
            "Operating system development"
        ],
        "answer": "Code hosting and collaboration",
        "skill": "GitHub"
    },

    {
        "section": "Web/API/Git",
        "question": "Which status code generally means 'Not Found'?",
        "options": [
            "200",
            "201",
            "404",
            "500"
        ],
        "answer": "404",
        "skill": "REST API"
    }
]


# =========================================================
# VERIFY QUESTION COUNT
# =========================================================

if len(ASSESSMENT_QUESTIONS) != ASSESSMENT_TOTAL_QUESTIONS:
    raise RuntimeError(
        f"Assessment question bank must contain "
        f"{ASSESSMENT_TOTAL_QUESTIONS} questions, "
        f"but contains {len(ASSESSMENT_QUESTIONS)}."
    )


# =========================================================
# CODING EVALUATION HELPERS
# =========================================================

BLOCKED_CODE_TOKENS = [
    "import os", "import sys", "import subprocess", "import socket",
    "import shutil", "import pathlib", "from os", "from sys", "from subprocess",
    "__import__", "eval(", "exec(", "open(", "socket.", "os.", "sys.",
    "subprocess.", "shutil.", "pathlib."
]


def evaluate_python_code(question, submitted_code):
    """Evaluate a coding answer with a short local timeout.

    This is suitable for a local/demo CareerAI project. A production system
    should run untrusted code inside a hardened isolated sandbox/container.
    """
    code = (submitted_code or "").strip()

    if not code:
        return False, "No code submitted."

    lowered = code.lower()
    for token in BLOCKED_CODE_TOKENS:
        if token.lower() in lowered:
            return False, "Blocked operation detected."

    full_code = code + "\n\n" + question.get("test_code", "")

    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(full_code)
            file_path = f.name

        result = subprocess.run(
            ["python", file_path],
            capture_output=True,
            text=True,
            timeout=3,
            cwd=os.path.dirname(file_path) or None
        )

        output = result.stdout.strip().replace("\r\n", "\n")
        expected = question.get("expected_output", "").strip().replace("\r\n", "\n")

        if result.returncode != 0:
            error = result.stderr.strip()[-1000:]
            return False, error or "Code execution failed."

        return output == expected, output

    except subprocess.TimeoutExpired:
        return False, "Execution timed out."
    except Exception as e:
        return False, str(e)
    finally:
        try:
            os.remove(file_path)
        except Exception:
            pass


def evaluate_sql_code(question, submitted_code):
    """Evaluate a read-only SQL answer against a fixed SQLite test database."""
    sql = (submitted_code or "").strip()

    if not sql:
        return False, "No SQL query submitted."

    normalized = sql.lower()
    forbidden = [
        "insert ", "update ", "delete ", "drop ", "alter ",
        "create ", "replace ", "attach ", "pragma ", "vacuum "
    ]

    if any(token in normalized for token in forbidden):
        return False, "Only read-only SQL queries are allowed."

    try:
        connection = sqlite3.connect(":memory:")
        cursor = connection.cursor()
        cursor.executescript(question.get("sql_schema", ""))
        cursor.execute(sql)
        rows = cursor.fetchall()

        formatted = []
        for row in rows:
            formatted.append("|".join(str(value) for value in row))

        output = "\n".join(formatted).strip()
        expected = question.get("expected_output", "").strip()
        return output == expected, output

    except Exception as e:
        return False, str(e)
    finally:
        try:
            connection.close()
        except Exception:
            pass


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    return render_template(
        "home.html"
    )
# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        # Temporary login validation
        # We will connect this to registration/database later.

        if email and password:

            session["logged_in"] = True
            session["user_email"] = email

            return redirect(
                url_for("career_setup")
            )

        return render_template(
            "login.html",
            error="Please enter your email and password."
        )

    return render_template(
        "login.html"
    )   


# =========================================================
# CAREER SETUP
# =========================================================

@app.route("/career-setup")
def career_setup():

    return render_template(
        "career_setup.html"
    )


# =========================================================
# ANALYZE PROFILE
# =========================================================

@app.route(
    "/analyze-profile",
    methods=["POST"]
)
def analyze_profile():

    name = request.form.get(
        "name"
    )

    email = request.form.get(
        "email"
    )

    qualification = request.form.get(
        "education"
    )

    graduation_year = request.form.get(
        "graduation_year"
    )

    target_role = request.form.get(
        "target_job"
    )

    experience = request.form.get(
        "experience"
    )

    skills = request.form.get(
        "skills",
        ""
    )

    career_goal = request.form.get(
        "career_goal"
    )

    resume = request.files.get(
        "resume"
    )

    resume_name = "No resume uploaded"

    resume_skills = []

    if resume and resume.filename:

        resume_name = resume.filename

        resume_path = os.path.join(
            app.root_path,
            "uploaded_resume_" + resume.filename
        )

        resume.save(
            resume_path
        )

        try:

            resume_analysis = analyze_resume(
                resume_path
            )

            resume_skills = resume_analysis.get(
                "detected_skills",
                []
            )

        except Exception as e:

            print(
                "Resume analysis error:",
                e
            )

            resume_skills = []

        try:

            os.remove(
                resume_path
            )

        except Exception:

            pass


    user_entered_skills = [

        skill.strip()

        for skill in skills.split(",")

        if skill.strip()

    ]


    combined_skills = (
        user_entered_skills.copy()
    )


    existing_skills_lower = [

        skill.lower()

        for skill in combined_skills

    ]


    for skill in resume_skills:

        if (

            skill.strip()

            and skill.strip().lower()
            not in existing_skills_lower

        ):

            combined_skills.append(
                skill.strip()
            )

            existing_skills_lower.append(
                skill.strip().lower()
            )


    skills_text = ", ".join(
        combined_skills
    )


    session["name"] = name

    session["email"] = email

    session["qualification"] = qualification

    session["graduation_year"] = graduation_year

    session["target_role"] = target_role

    session["experience"] = experience

    session["skills"] = skills_text

    session["career_goal"] = career_goal

    session["resume_name"] = resume_name

    session["resume_skills"] = resume_skills


    return render_template(

        "analyze_profile.html",

        name=name,

        email=email,

        qualification=qualification,

        graduation_year=graduation_year,

        target_role=target_role,

        experience=experience,

        skills=skills_text,

        career_goal=career_goal,

        resume_name=resume_name,

        resume_skills=resume_skills

    )


# =========================================================
# SKILL GAP ANALYSIS
# =========================================================

@app.route("/skill-gap")
def skill_gap():

    target_role = session.get(
        "target_role",
        ""
    )

    skills_text = session.get(
        "skills",
        ""
    )

    required_skills = SKILL_REQUIREMENTS.get(
        target_role,
        []
    )

    user_skills = [
        skill.strip()
        for skill in skills_text.split(",")
        if skill.strip()
    ]

    user_skills_lower = [
        skill.lower()
        for skill in user_skills
    ]

    matched_skills = []
    missing_skills = []

    for skill in required_skills:

        if skill.strip().lower() in user_skills_lower:

            matched_skills.append(
                skill
            )

        else:

            missing_skills.append(
                skill
            )

    # -----------------------------------------------------
    # AI SKILL GAP ANALYSIS
    # -----------------------------------------------------

    analysis = analyze_skills(
        user_skills,
        missing_skills,
        target_role
    )

    match_percentage = analysis.get(
        "match_percentage",
        0
    )

    readiness = analysis.get(
        "readiness",
        "Not Analyzed"
    )

    recommendation = analysis.get(
        "recommendation",
        "Complete the skill gap analysis to receive a personalized recommendation."
    )

    learning_priorities = analysis.get(
        "learning_priorities",
        []
    )

    strengths = analysis.get(
        "strengths",
        []
    )

    # -----------------------------------------------------
    # SAVE PROFILE SKILL GAP RESULTS
    # -----------------------------------------------------

    session["match_percentage"] = match_percentage
    session["readiness"] = readiness
    session["recommendation"] = recommendation
    session["learning_priorities"] = learning_priorities
    session["strengths"] = strengths
    session["missing_skills"] = missing_skills

    # -----------------------------------------------------
    # GET ASSESSMENT RESULTS
    #
    # Assessment Score and Current Skill Match
    # are kept as separate values.
    # -----------------------------------------------------

    assessment_completed = session.get(
        "assessment_completed",
        False
    )

    assessment_score = session.get(
        "assessment_score",
        0
    )

    assessment_total = session.get(
        "assessment_total",
        0
    )

    assessment_percentage = session.get(
        "assessment_percentage",
        0
    )

    assessment_level = session.get(
        "assessment_level",
        "Not Attempted"
    )

    assessment_recommendation = session.get(
        "assessment_recommendation",
        "Complete the assessment to receive a personalized recommendation."
    )

    assessment_weak_skills = session.get(
        "assessment_weak_skills",
        []
    )

    assessment_skill_results = session.get(
        "assessment_skill_results",
        {}
    )

    assessment_skill_percentages = session.get(
        "assessment_skill_percentages",
        {}
    )

    # -----------------------------------------------------
    # DISPLAY SKILL GAP PAGE
    # -----------------------------------------------------

    return render_template(

        "skill_gap.html",

        name=session.get(
            "name"
        ),

        target_role=target_role,

        user_skills=user_skills,

        required_skills=required_skills,

        matched_skills=matched_skills,

        missing_skills=missing_skills,

        # Profile / Resume Skill Match
        match_percentage=match_percentage,

        readiness=readiness,

        recommendation=recommendation,

        learning_priorities=learning_priorities,

        strengths=strengths,

        ai_analysis=analysis,

        # Assessment Results
        assessment_completed=assessment_completed,

        assessment_score=assessment_score,

        assessment_total=assessment_total,

        assessment_percentage=assessment_percentage,

        assessment_level=assessment_level,

        assessment_recommendation=assessment_recommendation,

        assessment_weak_skills=assessment_weak_skills,

        assessment_skill_results=assessment_skill_results,

        assessment_skill_percentages=assessment_skill_percentages

    )


# =========================================================
# ASSESSMENT INSTRUCTIONS
# =========================================================

@app.route("/assessment")
def assessment_instructions():

    target_role = session.get(
        "target_role",
        "Software Developer"
    )

    return render_template(

        "assessment_instructions.html",

        target_role=target_role

    )


# =========================================================
# SYSTEM CHECK PAGE
# =========================================================

@app.route("/assessment/system-check")
def assessment_system_check():

    target_role = session.get(
        "target_role",
        "Software Developer"
    )

    return render_template(

        "system_check.html",

        target_role=target_role

    )


# =========================================================
# START BUTTON FROM INSTRUCTIONS
#
# The student should NOT directly enter the assessment.
# They must first complete system checks.
# =========================================================

@app.route("/assessment/start")
def assessment_start():

    return redirect(
        url_for(
            "assessment_system_check"
        )
    )


# =========================================================
# COMPLETE SYSTEM CHECK
# =========================================================

@app.route(
    "/assessment/complete-system-check",
    methods=["POST"]
)
def complete_system_check():

    camera_ok = (
        request.form.get(
            "camera_ok"
        ) == "true"
    )

    microphone_ok = (
        request.form.get(
            "microphone_ok"
        ) == "true"
    )

    fullscreen_ok = (
        request.form.get(
            "fullscreen_ok"
        ) == "true"
    )

    permissions_ok = (
        request.form.get(
            "permissions_ok"
        ) == "true"
    )


    if not (

        camera_ok
        and microphone_ok
        and fullscreen_ok
        and permissions_ok

    ):

        return redirect(
            url_for(
                "assessment_system_check"
            )
        )


    # -----------------------------------------------------
    # STORE SYSTEM CHECK STATUS
    # -----------------------------------------------------

    session[
        "assessment_system_check_passed"
    ] = True


    session[
        "assessment_started"
    ] = False


    return redirect(
        url_for(
            "begin_assessment"
        )
    )


# =========================================================
# BEGIN 64-QUESTION ASSESSMENT
# =========================================================

@app.route("/assessment/begin")
def begin_assessment():

    system_check_passed = session.get(
        "assessment_system_check_passed",
        False
    )


    if not system_check_passed:

        return redirect(
            url_for(
                "assessment_system_check"
            )
        )


    target_role = session.get(
        "target_role",
        "Software Developer"
    )


    # -----------------------------------------------------
    # USE ALL 64 QUESTIONS
    # -----------------------------------------------------

    selected_questions = (
        ASSESSMENT_QUESTIONS.copy()
    )


    # -----------------------------------------------------
    # STORE QUESTIONS IN SESSION
    #
    # Correct answers stay server-side.
    # -----------------------------------------------------

    session[
        "assessment_question_ids"
    ] = list(range(len(selected_questions)))


    session[
        "assessment_started"
    ] = True

    session[
        "assessment_violations"
    ] = []


    assessment_start = datetime.now()

    session[
        "assessment_start_time"
    ] = assessment_start.isoformat()

    assessment_deadline = (
        assessment_start
        + timedelta(minutes=ASSESSMENT_DURATION_MINUTES)
    )

    session[
        "assessment_deadline"
    ] = assessment_deadline.isoformat()

    session[
        "assessment_duration_minutes"
    ] = ASSESSMENT_DURATION_MINUTES


    # -----------------------------------------------------
    # DATA SENT TO HTML
    #
    # Correct answers are NOT sent.
    # -----------------------------------------------------

    questions_for_html = []


    for index, question in enumerate(
        selected_questions
    ):

        questions_for_html.append({

            "id": index,

            "section": question[
                "section"
            ],

            "question": question[
                "question"
            ],

            "options": question.get(
                "options",
                []
            ),

            "skill": question[
                "skill"
            ],

            "type": question.get(
                "type",
                "mcq"
            ),

            "language": question.get(
                "language",
                ""
            ),

            "starter_code": question.get(
                "starter_code",
                ""
            ),

            "sql_schema": question.get(
                "sql_schema",
                ""
            )

        })


    is_reassessment = (
        request.args.get(
            "reassessment"
        ) == "true"
    )


    return render_template(

        "assessment.html",

        target_role=target_role,

        questions=questions_for_html,

        total_questions=ASSESSMENT_TOTAL_QUESTIONS,

        duration_minutes=ASSESSMENT_DURATION_MINUTES,

        assessment_deadline=assessment_deadline.isoformat(),

        sections=sorted(
            list(
                set(
                    question["section"]
                    for question
                    in selected_questions
                )
            )
        ),

        is_reassessment=is_reassessment

    )


# =========================================================
# RUN CODE / QUERY DURING ASSESSMENT
# =========================================================

@app.route("/assessment/run-code", methods=["POST"])
def run_assessment_code():
    """Run one submitted coding answer against its server-side test case.

    This is intended for the local/demo project. Production deployments
    should execute untrusted code inside a hardened sandbox/container.
    """
    if not session.get("assessment_started", False):
        return {"ok": False, "message": "Assessment is not active."}, 403

    data = request.get_json(silent=True) or {}

    try:
        question_index = int(data.get("question_index"))
    except (TypeError, ValueError):
        return {"ok": False, "message": "Invalid question."}, 400

    submitted_code = data.get("code", "")
    questions = ASSESSMENT_QUESTIONS

    if question_index < 0 or question_index >= len(questions):
        return {"ok": False, "message": "Invalid question."}, 400

    question = questions[question_index]
    question_type = question.get("type", "mcq")

    if question_type not in ("coding", "sql"):
        return {"ok": False, "message": "This is not a coding question."}, 400

    deadline_text = session.get("assessment_deadline")
    if deadline_text:
        try:
            if datetime.now() > datetime.fromisoformat(deadline_text):
                return {"ok": False, "message": "Assessment time has expired."}, 403
        except ValueError:
            pass

    if question_type == "sql":
        is_correct, output = evaluate_sql_code(question, submitted_code)
    else:
        is_correct, output = evaluate_python_code(question, submitted_code)

    return {
        "ok": True,
        "correct": is_correct,
        "output": output if output else "No output.",
        "message": "Correct output." if is_correct else "Output does not match the test case."
    }


# =========================================================
# ASSESSMENT VIOLATION LOG
# =========================================================

@app.route("/assessment/violation", methods=["POST"])
def assessment_violation():
    """Record client-side assessment violations in the current session."""
    if not session.get("assessment_started", False):
        return {"ok": False}, 403

    data = request.get_json(silent=True) or {}
    reason = str(data.get("reason", "Unknown violation"))[:120]

    violations = session.get("assessment_violations", [])
    violations.append({
        "reason": reason,
        "time": datetime.now().isoformat()
    })

    # Keep only the most recent 20 records to avoid oversized sessions.
    session["assessment_violations"] = violations[-20:]
    session.modified = True

    return {
        "ok": True,
        "count": len(session["assessment_violations"])
    }


# =========================================================
# OLD / DIRECT START URL
#
# If somebody manually enters /assessment/start,
# they are sent through the system check.
# =========================================================

@app.route("/assessment/test")
def assessment_test_redirect():

    return redirect(
        url_for(
            "begin_assessment"
        )
    )


# =========================================================
# SUBMIT ASSESSMENT
# =========================================================

@app.route(
    "/submit-assessment",
    methods=["POST"]
)
def submit_assessment():

    target_role = session.get(
        "target_role",
        "Software Developer"
    )


    questions = ASSESSMENT_QUESTIONS


    # -----------------------------------------------------
    # SAFETY CHECK
    # -----------------------------------------------------

    if not questions:

        return (
            "Assessment session expired. "
            "Please start the assessment again."
        )

    # Server-side timer enforcement. The browser timer is only the display;
    # this deadline is authoritative for the active attempt.
    time_expired = False
    deadline_text = session.get("assessment_deadline")

    if deadline_text:
        try:
            time_expired = datetime.now() > datetime.fromisoformat(
                deadline_text
            )
        except ValueError:
            time_expired = False


    # -----------------------------------------------------
    # ENSURE THE CURRENT ASSESSMENT IS 64 QUESTIONS
    # -----------------------------------------------------

    total_questions = len(
        questions
    )


    # -----------------------------------------------------
    # CALCULATE SCORE
    # -----------------------------------------------------

    score = 0

    wrong_answers = []

    skill_results = {}


    for index, question in enumerate(
        questions
    ):

        question_type = question.get(
            "type",
            "mcq"
        )

        if question_type in (
            "coding",
            "sql"
        ):
            submitted_answer = request.form.get(
                f"question_{index}",
                ""
            )

            if question_type == "sql":
                is_correct, execution_output = evaluate_sql_code(
                    question,
                    submitted_answer
                )
            else:
                is_correct, execution_output = evaluate_python_code(
                    question,
                    submitted_answer
                )

            correct_answer = question.get(
                "expected_output",
                ""
            )
        else:
            submitted_answer = request.form.get(
                f"question_{index}"
            )
            correct_answer = question[
                "answer"
            ]
            is_correct = submitted_answer == correct_answer
            execution_output = ""

        skill = question[
            "skill"
        ]

        if skill not in skill_results:
            skill_results[skill] = {
                "correct": 0,
                "total": 0
            }

        skill_results[skill][
            "total"
        ] += 1

        if is_correct:
            score += 1
            skill_results[skill][
                "correct"
            ] += 1
        else:
            wrong_answers.append({
                "question": question[
                    "question"
                ],
                "your_answer": (
                    submitted_answer
                    if submitted_answer
                    else "Not answered"
                ),
                "correct_answer": correct_answer,
                "skill": skill,
                "type": question_type,
                "execution_output": execution_output
            })

    # -----------------------------------------------------
    # CALCULATE PERCENTAGE
    # -----------------------------------------------------

    if total_questions > 0:

        assessment_percentage = round(

            (
                score
                / total_questions
            ) * 100

        )

    else:

        assessment_percentage = 0


    # =====================================================
    # ASSESSMENT LEVEL
    # =====================================================

    if assessment_percentage >= 80:

        assessment_level = "Excellent"

        assessment_recommendation = (

            f"Excellent performance for a "
            f"{target_role} career. "
            "You have demonstrated strong "
            "technical understanding. "
            "Focus next on advanced concepts, "
            "real-world projects and interview "
            "preparation."

        )

    elif assessment_percentage >= 60:

        assessment_level = "Good"

        assessment_recommendation = (

            f"You have a good technical foundation "
            f"for a {target_role} role. "
            "Strengthen the topics where you made "
            "mistakes and practice them through "
            "hands-on projects."

        )

    elif assessment_percentage >= 40:

        assessment_level = "Needs Improvement"

        assessment_recommendation = (

            f"You have started building the "
            f"knowledge required for a {target_role} "
            "career. Focus on your weak technical "
            "areas and revise the fundamentals "
            "before moving to advanced topics."

        )

    else:

        assessment_level = "Beginner"

        assessment_recommendation = (

            f"Your assessment shows that you need "
            f"to strengthen the fundamentals for "
            f"a {target_role} career. "
            "Start with the core concepts, practice "
            "regularly and gradually move toward "
            "advanced topics."

        )


    # =====================================================
    # IDENTIFY WEAK SKILLS
    # =====================================================

    weak_skills = []


    for skill, result in skill_results.items():

        if result["correct"] < result["total"]:

            weak_skills.append(
                skill
            )


    # =====================================================
    # SKILL-WISE RESULTS
    # =====================================================

    skill_percentages = {}


    for skill, result in skill_results.items():

        if result["total"] > 0:

            skill_percentages[skill] = round(

                (
                    result["correct"]
                    / result["total"]
                ) * 100

            )

        else:

            skill_percentages[skill] = 0


    # =====================================================
    # RE-ASSESSMENT COMPARISON
    # =====================================================

    previous_score = session.get(
        "assessment_percentage"
    )


    improvement = None


    if previous_score is not None:

        improvement = (

            assessment_percentage
            - previous_score

        )


    # =====================================================
    # SAVE RESULTS
    # =====================================================

    session[
        "assessment_score"
    ] = score


    session[
        "assessment_total"
    ] = total_questions


    session[
        "assessment_percentage"
    ] = assessment_percentage


    session[
        "assessment_level"
    ] = assessment_level


    session[
        "assessment_recommendation"
    ] = assessment_recommendation


    session[
        "assessment_weak_skills"
    ] = weak_skills


    

    session[
        "assessment_skill_results"
    ] = skill_results


    session[
        "assessment_skill_percentages"
    ] = skill_percentages


    session[
        "assessment_completed"
    ] = True


    session[
        "assessment_started"
    ] = False


    # -----------------------------------------------------
    # CLEAR ACTIVE ASSESSMENT STATE
    # -----------------------------------------------------

    session.pop(
        "assessment_system_check_passed",
        None
    )

    session.pop(
        "assessment_question_ids",
        None
    )

    session.pop(
        "assessment_start_time",
        None
    )

    session.pop(
        "assessment_deadline",
        None
    )


    # =====================================================
    # DISPLAY RESULT
    # =====================================================

    assessment_violation_count = len(
        session.get("assessment_violations", [])
    )
    
    session.pop("assessment_violations", None)

    return render_template(

        "assessment_result.html",

        target_role=target_role,

        score=score,

        total_questions=total_questions,

        assessment_percentage=
            assessment_percentage,

        assessment_level=
            assessment_level,

        assessment_recommendation=
            assessment_recommendation,

        weak_skills=
            weak_skills,

        wrong_answers=
            wrong_answers,

        previous_score=
            previous_score,

        improvement=
            improvement,

        skill_results=
            skill_results,

        skill_percentages=
            skill_percentages,

        time_expired=time_expired,

        assessment_violation_count=assessment_violation_count

    )


# =========================================================
# PERSONALIZED LEARNING ROADMAP
# =========================================================

@app.route("/roadmap")
def roadmap():

    target_role = session.get(
        "target_role",
        "Software Developer"
    )

    # -----------------------------------------------------
    # PROFILE / RESUME SKILL GAP RESULTS
    # -----------------------------------------------------

    match_percentage = session.get(
        "match_percentage",
        0
    )

    readiness = session.get(
        "readiness",
        "Not Analyzed"
    )

    recommendation = session.get(
        "recommendation",
        "Complete the skill gap analysis to receive a personalized recommendation."
    )

    learning_priorities = session.get(
        "learning_priorities",
        []
    )

    strengths = session.get(
        "strengths",
        []
    )

    missing_skills = session.get(
        "missing_skills",
        []
    )

    # -----------------------------------------------------
    # ASSESSMENT RESULTS
    # -----------------------------------------------------

    assessment_completed = session.get(
        "assessment_completed",
        False
    )

    assessment_score = session.get(
        "assessment_score",
        0
    )

    assessment_total = session.get(
        "assessment_total",
        0
    )

    assessment_percentage = session.get(
        "assessment_percentage",
        0
    )

    assessment_level = session.get(
        "assessment_level",
        "Not Attempted"
    )

    assessment_recommendation = session.get(
        "assessment_recommendation",
        "Complete the assessment to receive a personalized recommendation."
    )

    assessment_weak_skills = session.get(
        "assessment_weak_skills",
        []
    )

    assessment_skill_results = session.get(
        "assessment_skill_results",
        {}
    )

    assessment_skill_percentages = session.get(
        "assessment_skill_percentages",
        {}
    )

    # -----------------------------------------------------
    # COMBINE PROFILE GAPS + ASSESSMENT WEAK AREAS
    # -----------------------------------------------------

    priority_skills = []

    for skill in missing_skills:

        if skill not in priority_skills:

            priority_skills.append(
                skill
            )

    for skill in assessment_weak_skills:

        if skill not in priority_skills:

            priority_skills.append(
                skill
            )

    # -----------------------------------------------------
    # READINESS DISPLAY
    # -----------------------------------------------------

    if assessment_completed:

        if readiness == "Not Analyzed":

            roadmap_readiness = assessment_level

        else:

            roadmap_readiness = readiness

    else:

        roadmap_readiness = readiness

    # -----------------------------------------------------
    # DISPLAY PERSONALIZED ROADMAP
    # -----------------------------------------------------

    return render_template(

        "roadmap.html",

        target_role=target_role,

        # Profile skill match
        match_percentage=match_percentage,

        readiness=roadmap_readiness,

        recommendation=recommendation,

        learning_priorities=learning_priorities,

        strengths=strengths,

        missing_skills=missing_skills,

        priority_skills=priority_skills,

        # Assessment results
        assessment_completed=assessment_completed,

        assessment_score=assessment_score,

        assessment_total=assessment_total,

        assessment_percentage=assessment_percentage,

        assessment_level=assessment_level,

        assessment_recommendation=assessment_recommendation,

        assessment_weak_skills=assessment_weak_skills,

        assessment_skill_results=assessment_skill_results,

        assessment_skill_percentages=assessment_skill_percentages

    )


# =========================================================
# RE-ASSESSMENT
# =========================================================

@app.route("/reassessment")
def reassessment():

    # Force a new system check before re-assessment.

    session[
        "assessment_system_check_passed"
    ] = False


    return redirect(
        url_for(
            "assessment_system_check"
        )
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    target_role = session.get(
        "target_role",
        "Software Developer"
    )


    readiness_score = session.get(
        "match_percentage",
        0
    )


    readiness_level = session.get(
        "readiness",
        "Not Analyzed"
    )


    learning_priorities = session.get(
        "learning_priorities",
        []
    )


    missing_skills = session.get(
        "missing_skills",
        []
    )


    strengths = session.get(
        "strengths",
        []
    )


    assessment_percentage = session.get(
        "assessment_percentage",
        0
    )


    assessment_level = session.get(
        "assessment_level",
        "Not Attempted"
    )


    assessment_completed = session.get(
        "assessment_completed",
        False
    )


    assessment_score = session.get(
        "assessment_score",
        0
    )


    assessment_total = session.get(
        "assessment_total",
        0
    )


    return render_template(

        "dashboard.html",

        target_role=target_role,

        readiness_score=
            readiness_score,

        readiness_level=
            readiness_level,

        learning_priorities=
            learning_priorities,

        missing_skills=
            missing_skills,

        strengths=
            strengths,

        assessment_percentage=
            assessment_percentage,

        assessment_level=
            assessment_level,

        assessment_completed=
            assessment_completed,

        assessment_score=
            assessment_score,

        assessment_total=
            assessment_total

    )



# =========================================================
# COURSES MODULE
# =========================================================

@app.route("/courses")
def courses():

    all_courses = get_all_courses()

    target_role = session.get(
        "target_role",
        "Software Developer"
    )

    # Get the student's existing profile/assessment gaps.
    missing_skills = session.get(
        "missing_skills",
        []
    )

    assessment_weak_skills = session.get(
        "assessment_weak_skills",
        []
    )

    # Combine both sources into one personalized skill list.
    priority_skills = []

    for skill in missing_skills + assessment_weak_skills:

        if skill and skill not in priority_skills:

            priority_skills.append(
                skill
            )

    # Courses matching the student's target role.
    role_courses = get_courses_by_role(
        target_role
    )

    # Courses matching the student's weak/missing skills.
    recommended_courses = []

    for skill in priority_skills:

        for course in get_courses_by_skill(skill):

            if course not in recommended_courses:

                recommended_courses.append(
                    course
                )

    # If no weak/missing skills are available yet,
    # recommend courses for the selected role.
    if not recommended_courses:

        recommended_courses = role_courses[:]

    return render_template(

        "courses.html",

        courses=all_courses,

        recommended_courses=recommended_courses,

        role_courses=role_courses,

        free_courses=get_free_courses(),

        paid_courses=get_paid_courses(),

        target_role=target_role,

        priority_skills=priority_skills

    )


# =========================================================
# COURSE DETAILS
# =========================================================

@app.route("/course/<course_id>")
def course_detail(course_id):
    course = get_course_by_id(course_id)
    if course is None:
        return "Course not found.", 404

    user_email = session.get("user_email")
    enrolled_ids = get_enrolled_course_ids(user_email) if user_email else []

    return render_template(
        "course_detail.html",
        course=course,
        is_enrolled=course_id in enrolled_ids
    )


# =========================================================
# ENROLL IN COURSE
# =========================================================
@app.route("/enroll/<course_id>", methods=["GET", "POST"])
def enroll_course(course_id):
    user_email = session.get("user_email")
    if not user_email:
        return redirect(url_for("login"))

    course = get_course_by_id(course_id)
    if course is None:
        return "Course not found.", 404

    if str(course.get("type", "")).lower() == "paid":
        return redirect(url_for("payment_page", course_id=course_id))

    save_enrollment(user_email, course_id)
    return redirect(url_for("my_courses"))


# =========================================================
# DEMO PAYMENT PAGE
# =========================================================

@app.route("/payment/<course_id>", methods=["GET", "POST"])
def payment_page(course_id):
    user_email = session.get("user_email")

    if not user_email:
        return redirect(url_for("login"))

    course = get_course_by_id(course_id)

    if course is None:
        return "Course not found.", 404

    if str(course.get("type", "")).lower() != "paid":
        return redirect(url_for("enroll_course", course_id=course_id))

    # Already enrolled? Open My Courses.
    if course_id in get_enrolled_course_ids(user_email):
        return redirect(url_for("my_courses"))

    if request.method == "POST":
        # Demo-only payment simulation.
        # No real payment is processed.
        save_enrollment(user_email, course_id)

        return redirect(url_for("my_courses"))

    return render_template("payment.html", course=course)
# =========================================================
# PROCESS DEMO PAYMENT
# =========================================================
@app.route("/payment/<course_id>/process", methods=["POST"])
def process_payment(course_id):
    user_email = session.get("user_email")
    if not user_email:
        return redirect(url_for("login"))

    course = get_course_by_id(course_id)
    if course is None:
        return "Course not found.", 404

    if str(course.get("type", "")).lower() != "paid":
        return redirect(url_for("enroll_course", course_id=course_id))

    # Demo payment only. Never store card details.
    save_enrollment(user_email, course_id)
    return redirect(url_for("my_courses"))


# =========================================================
# MY COURSES
# =========================================================
@app.route("/my-courses")
def my_courses():
    user_email = session.get("user_email")
    if not user_email:
        return redirect(url_for("login"))

    enrolled_ids = get_enrolled_course_ids(user_email)
    enrolled_courses = []

    for course_id in enrolled_ids:
        course = get_course_by_id(course_id)
        if not course:
            continue

        completed_lessons = get_completed_lessons(user_email, course_id)
        total_lessons = get_total_lessons(course_id)
        progress_percentage = round(len(completed_lessons) / total_lessons * 100) if total_lessons else 0

        course_data = dict(course)
        course_data["completed_lessons"] = len(completed_lessons)
        course_data["total_lessons"] = total_lessons
        course_data["progress_percentage"] = progress_percentage
        enrolled_courses.append(course_data)

    return render_template("my_courses.html", enrolled_courses=enrolled_courses)


# =========================================================
# COURSE LEARNING
# =========================================================

@app.route("/course/<course_id>/learn")
def course_learning(course_id):
    user_email = session.get("user_email")

    if not user_email:
        return redirect(url_for("login"))

    course = get_course_by_id(course_id)

    if course is None:
        return "Course not found.", 404

    if course_id not in get_enrolled_course_ids(user_email):
        return redirect(url_for("course_detail", course_id=course_id))

    lessons = get_course_lessons(course_id)
    completed_lessons = get_completed_lessons(user_email, course_id)

    # Compare lesson IDs consistently as strings.
    completed_lessons = [str(lesson_id) for lesson_id in completed_lessons]

    completed_count = len(completed_lessons)
    total_lessons = len(lessons)

    progress_percentage = (
        round(completed_count / total_lessons * 100)
        if total_lessons else 0
    )

    return render_template(
        "course_learning.html",
        course=course,
        course_id=course_id,
        lessons=lessons,
        completed_lessons=completed_lessons,
        completed_count=completed_count,
        total_lessons=total_lessons,
        progress_percentage=progress_percentage
    )


# =========================================================
# COMPLETE COURSE LESSON (single route; persistent database)
# =========================================================
@app.route("/course/<course_id>/lesson/<lesson_id>/complete", methods=["POST"])
def complete_course_lesson(course_id, lesson_id):
    user_email = session.get("user_email")
    if not user_email:
        return redirect(url_for("login"))

    course = get_course_by_id(course_id)
    if course is None:
        return "Course not found.", 404

    if course_id not in get_enrolled_course_ids(user_email):
        return "You are not enrolled in this course.", 403

    lesson = get_lesson(course_id, lesson_id)
    if lesson is None:
        return "Lesson not found.", 404

    save_completed_lesson(user_email, course_id, lesson_id)
    return redirect(url_for("course_learning", course_id=course_id))


# =========================================================
# CERTIFICATES
# =========================================================
@app.route("/certificates")
def certificates():
    user_email = session.get("user_email")
    if not user_email:
        return redirect(url_for("login"))

    certificates_list = []
    for course_id in get_enrolled_course_ids(user_email):
        course = get_course_by_id(course_id)
        if course is None:
            continue

        total_lessons = get_total_lessons(course_id)
        completed_count = len(get_completed_lessons(user_email, course_id))
        if total_lessons > 0 and completed_count >= total_lessons:
            certificates_list.append({
                "course": course,
                "completed_count": completed_count,
                "total_lessons": total_lessons
            })

    return render_template("certificates.html", certificates=certificates_list)


# =========================================================
# VIEW CERTIFICATE
# =========================================================
@app.route("/certificate/<course_id>")
def view_certificate(course_id):
    user_email = session.get("user_email")
    if not user_email:
        return redirect(url_for("login"))

    course = get_course_by_id(course_id)
    if course is None:
        return "Course not found.", 404

    if course_id not in get_enrolled_course_ids(user_email):
        return "You are not enrolled in this course.", 403

    completed_count = len(get_completed_lessons(user_email, course_id))
    total_lessons = get_total_lessons(course_id)
    if total_lessons == 0 or completed_count < total_lessons:
        return redirect(url_for("course_learning", course_id=course_id))

    student_name = session.get("name", "").strip()
    if not student_name:
        student_name = user_email.split("@")[0].replace(".", " ").replace("_", " ").title()

    certificate_id = "CAI-" + course_id.replace("-", "").upper() + "-CERT"
    completion_date = datetime.now().strftime("%d %B %Y")

    return render_template(
        "certificate.html",
        student_name=student_name,
        course=course,
        course_name=course.get("title", course.get("name", course_id)),
        certificate_id=certificate_id,
        completion_date=completion_date
    )


if __name__ == "__main__":
    init_course_database()
    init_progress_database()
    app.run(debug=True)    
    