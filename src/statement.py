'''
Name: statement.py
Author: Michael Deckebach
Date: 2022-10-01
Description: Implementation of the following classes:

    StatementFactory - Abstract class to create various SQL statements
    Statement - Interface providing the basic structure of a SQL statement
    AlterStatement - An ALTER TABLE statement
    BeginStatment - A BEGIN TRANSACTION statement
    CreateStatement - A CREATE statement (CREATE DATABASE or CREATE TABLE)
    CommitStatement = A COMMIT statement
    DeleteStatement - A DELETE statement (DELETE FROM <table> WHERE <condition>)
    DropStatement - A DROP statement (DROP DATABASE or DROP TABLE)
    InsertStatement - An INSERT statement (INSERT INTO <table> VALUES(<value>,...))
    SelectStatement - A SELECT statement (SELECT * FROM <table> [WHERE <condition>])
    UpdateStatement - An UPDATE statement (UPDATE <table> SET <field> = <value> WHERE <condition>)
    UseStatement - A USE statement (USE <database>)

'''

import re

from database import Database
from table import Table
import utils


# Class used to instantiate various Statement child classes, depending
# on the type of SQL command submitted. Also checks for and throws an
# error if unsupported SQL commands are submitted. Current support is
# only for ALTER, CREATE, DROP, SELECT, and USE statements.

class StatementFactory:

    def __init__(self):
        pass

    def make_statement(self, str):

        if self._is_alter_statement(str):
            return AlterStatement(str)

        elif self._is_begin_statement(str):
            return BeginStatement(str)
        
        elif self._is_create_statement(str):
            return CreateStatement(str)

        elif self._is_commit_statement(str):
            return CommitStatement(str)

        elif self._is_delete_statement(str):
            return DeleteStatement(str)

        elif self._is_drop_statement(str):
            return DropStatement(str)

        elif self._is_insert_statement(str):
            return InsertStatement(str)

        elif self._is_select_statement(str):
            return SelectStatement(str)

        elif self._is_update_statement(str):
            return UpdateStatement(str)

        elif self._is_use_statement(str):
            return UseStatement(str)

        else:
            raise Exception("Command not supported: " + str)

    def _is_alter_statement(self, str):
        return bool(re.search(r'(?i)(ALTER )(.*)', str))

    def _is_begin_statement(self, str):
        return bool(re.search(r'(?i)(BEGIN TRANSACTION)', str))

    def _is_create_statement(self, str):
        return bool(re.search(r'(?i)(CREATE )(.*)', str))

    def _is_commit_statement(self, str):
        return bool(re.search(r'(?i)(COMMIT)', str))

    def _is_delete_statement(self, str):
        return bool(re.search(r'(?i)(DELETE FROM )(.*)', str))

    def _is_drop_statement(self, str):
        return bool(re.search(r'(?i)(DROP )\w{2}', str))

    def _is_insert_statement(self, str):
        return bool(re.search(r'(?i)(INSERT INTO )(.*)', str))

    def _is_select_statement(self, str):
        return bool(re.search(r'(?i)(SELECT )(.*)', str))

    def _is_update_statement(sefl, str):
        return bool(re.search(r'(?i)(UPDATE )(.*)( SET )(.*)', str))

    def _is_use_statement(self, str):
        return bool(re.search(r'(?i)(USE )\w{2}', str))


# Interface for Statement classes. Statement.str is the raw string the user
# submitted.
class Statement:

    def __init__(self, str):
        self.str = str
        self.parsed = str.split()
        self.num_words = len(self.parsed)
        self.start_transaction = False
        self.end_transaction = False

    def execute(self):
        pass

    def get_locked_tables(self):
        return self.locked_tables

    def get_table_name(self):
        pass
    
    def set_table_name(self, new_name):
        pass


class AlterStatement(Statement):

    def __init__(self, str):
        Statement.__init__(self, str)       
        self.parse_clauses()

    def execute(self):
        Table(self.from_clause).alter(self.new_field)

    def parse_clauses(self):
        self.from_clause = re.search(r'(?<=ALTER TABLE\s)(.*)(?=\sADD)', self.str, re.I).group()
        self.new_field = re.search(r'(?<=ADD\s)(.*)', self.str, re.I).group().strip()

    def get_table_name(self):
        return self.from_clause

    def set_table_name(self, new_name):
        self.from_clause = new_name


class BeginStatement(Statement):

    def __init__(self, str):
        Statement.__init__(self, str)
        self.start_transaction = True

    def execute(self):
        print("Transaction starts.")


class CreateStatement(Statement):

    def __init__(self, str):
        Statement.__init__(self, str)

        if not self.min_size():
            raise Exception("Invalid CREATE command. Please check syntax")

        self.type = self.parsed[1].upper()
        self.object_name = self.parsed[2]

        if not self.correct_size():
            raise Exception("Invalid CREATE command. Please check syntax")

        if not self.valid_type():
            raise Exception("Invalid CREATE command. Valid objects are CREATE DATABASE <name> or CREATE TABLE <name>")

    def correct_size(self):
        if self.type == 'DATABASE':
            return self.num_words == 3
        elif self.type == 'TABLE':
            return self.num_words >= 3
 
    def execute(self):        
        if self.type == 'DATABASE':
            Database(self.object_name).create()
        elif self.type == 'TABLE':

            # Generate a list of fields and types
            field_str = ' '.join(self.parsed[3:])
            fields = self.parse_fields(field_str)
            
            Table(self.object_name).create(fields)

    def min_size(self):
        return self.num_words >= 3

    def parse_fields(self, str):
        fields = re.findall(r'(?![(].*)[^,]*(?=.*[)]$)', str)
        return [i.strip() for i in fields if i != '']

    def valid_type(self):
        return self.type in utils.KEYWORDS_OBJECTS

    def get_table_name(self):
        if self.type == 'TABLE':
            return self.object_name
        else:
            raise Exception("Error: cannot get a table name for a database-specific command")

    def set_table_name(self, new_name):
        if self.type == 'TABLE':
            self.object_name = new_name

class CommitStatement(Statement):

    def __init__(self, str):
        Statement.__init__(self, str)
        self.end_transaction = True
        self.commits = 0

    def execute(self):
        if self.commits == 0:
            print("Transaction abort.")
        else:
            print("Transaction committed.")


class DeleteStatement(Statement):

    def __init__(self, str):
        Statement.__init__(self, str)
        self.parse_clauses()

    def execute(self):
        Table(self.table_name).delete(self.condition)
        pass

    def parse_clauses(self):
        self.table_name = re.search(r'(?<=DELETE FROM\s)(\w+)', self.str, re.I).group()
        self.condition = re.search(r'(?<=WHERE\s)(.*)', self.str, re.I).group()

    def get_table_name(self):
        return self.table_name

    def set_table_name(self, new_name):
        self.table_name = new_name


class DropStatement(Statement):

    def __init__(self, str):
        Statement.__init__(self, str)

        if not self.correct_size():
            raise Exception("Invalid DROP command. Please check syntax")

        self.type = self.parsed[1].upper()
        self.object_name = self.parsed[2]

        if not self.valid_type():
            raise Exception("Invalid DROP command. Valid objects are DROP DATABASE <name> or DROP TABLE <name>")

    def correct_size(self):
        return self.num_words == 3

    def execute(self):
        if self.type == 'DATABASE':
            Database(self.object_name).drop()
            pass
        elif self.type == 'TABLE':
            Table(self.object_name).drop()
            pass

    def valid_type(self):
        return self.type in utils.KEYWORDS_OBJECTS

    def get_table_name(self):
        if self.type == 'TABLE':
            return self.object_name
        else:
            raise Exception("Error: cannot get a table name for a database-specific command")

    def set_table_name(self, new_name):
        if self.type == 'TABLE':
            self.object_name = new_name

class InsertStatement(Statement):

    def __init__(self, str):
        Statement.__init__(self, str)
        self.parse_clauses()
    
    def execute(self):
        Table(self.table_name).insert(self.values)

    def parse_clauses(self):
        # Parses the raw string using REGEX to isolate the table_name
        # and the tuple values to be inserted for downstream use
        self.table_name = re.search(r'(?<=INSERT INTO\s)(.*)(?=\sVALUES)', self.str, re.I).group()
        
        temp = re.search(r'(?<=\().*(?=\))', self.str).group().split(',')
        self.values = [i.strip().replace("'", '') for i in temp if i != '']

    def get_table_name(self):
        return self.table_name

    def set_table_name(self, new_name):
        self.table_name = new_name
        

class SelectStatement(Statement):

    def __init__(self, str):
        Statement.__init__(self, str)      
        self.parse_clauses()

    def execute(self):
        tbl = Table(self.left_table_name, alias=self.left_table_alias)
        tbl.select(self.select_clause, self.where_clause, self.join_type, self.right_table_name, self.right_table_alias)

    def parse_clauses(self):
        # Parses the raw string using REGEX to isolate the contents of the 
        # SELECT clause (select_clause) and FROM clause (from_clause) for
        # downstream use
        self.select_clause = re.search(r'(?<=SELECT\s)(.*)(?=\sFROM)', self.str, re.I).group()
        self.select_clause = self.select_clause.split(',')
        self.select_clause = [i.strip() for i in self.select_clause]
        
        self.from_clause = re.search(r'(?<=FROM\s)[\w\s,]+?(?=(\s(ON|WHERE))|$)', self.str, re.I).group()
        self.where_clause = re.search(r'(?<=WHERE|...ON)\s(.*)', self.str, re.I)
        
        if self.where_clause:
            self.where_clause = self.where_clause.group()

        self.set_join_type()
        self.parse_from_clause()

    def set_join_type(self):
        # Helper function to parse join type of a SELECT clause, currently supports
        # only INNER JOIN and LEFT OUTER JOIN syntax
        self.join_type = None
        if re.search(r',|INNER JOIN', self.from_clause, re.I):
            self.join_type = 'INNER'
        elif re.search(r'LEFT OUTER JOIN', self.from_clause, re.I):
            self.join_type = 'LEFT'

    def parse_from_clause(self):
        # Helper function to pull out table names and aliases from a FROM clause
        # with consideration for whether it contains a JOIN
        self.right_table = None
        self.right_table_name = None
        self.right_table_alias = None

        # Split up clause based on the JOIN keywords (or lack thereof)
        from_split = re.split(r'(INNER JOIN|LEFT OUTER JOIN|,)', self.from_clause, maxsplit=3, flags=re.I)

        # This is the entire string up to any JOIN keyword, split into a list
        left_table = from_split[0].strip().split()

        if len(from_split) == 1:
            right_table = None
        else:
            right_table = from_split[2].strip().split()
            self.right_table_name = right_table[0]

            # If len == 2, then that means the user entered an alias
            if len(right_table) == 2:
                self.right_table_alias = right_table[1]
            else:
                self.right_table_alias = None
        
        self.left_table_name = left_table[0]

        if len(left_table) == 2:
            self.left_table_alias = left_table[1]
        else:
            self.left_table_alias = None  

    def get_table_name(self):
        if self.join_type != None:
            raise Exception("JOINs not supported with Transactions. Please restrict queries to single tables")
        else:
            return self.left_table_name

    def set_table_name(self, new_name):
        if self.join_type != None:
            self.left_table_name == new_name

class UpdateStatement(Statement):

    def __init__(self, str):
        Statement.__init__(self, str)
        self.parse_clauses()

    def execute(self):
        Table(self.table_name).update(self.target_field, self.target_value, self.condition)

    def parse_clauses(self):
        self.table_name = re.search(r'(?<=UPDATE\s)(.*)(?=\sSET)', self.str, re.I).group()
        self.target_field = re.search(r'(?<=SET\s)(.*?)(?=\s=)', self.str, re.I).group().replace("'", '')
        self.target_value = re.search(r'(?<==\s)(.*)(?=\sWHERE)', self.str, re.I).group().replace("'", '')
        self.condition = re.search(r'(?<=WHERE\s)(.*)', self.str, re.I).group()

    def get_table_name(self):
        return self.table_name

    def set_table_name(self, new_name):
        self.table_name = new_name

class UseStatement(Statement):

    def __init__(self, str):
        Statement.__init__(self, str)

        if not self.correct_size():
            raise Exception("Invalid USE command. Please check syntax")

        self.object_name = self.parsed[1]

    def correct_size(self):
        return self.num_words == 2

    def execute(self):
        Database(self.object_name).use()
        pass