from collections import UserDict
from datetime import datetime, date, timedelta
from functools import wraps
import pickle

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)
    
    def __eq__(self, other):
        # adding equality method to simplify further usage, since Field class is ment for simple types of data
        # and it will be conveniant to use "in", "==" and other comparisons similar to primitive types. 
        if isinstance(other, Field):
            return self.value == other.value
        return False
    
    # defining the method to ensure correct serialization of value
    def __getstate__(self):
        return self.__dict__
    
    # defining the method to ensure correct deserialization of value
    def __setstate__(self, state):
        self.__dict__.update(state)

# Since classes Name, Phone and Birthday inherit from Field, they inherit the __getstate__ and __setstate__ methods

class Name(Field):
    # This class represents the name of a contact, ensures it has a value attribute. Parent class is Field
    def __init__(self, value):
        if not value.strip():
            raise ValueError("Name field cannot be empty.")
        super().__init__(value)

class Phone(Field):
    # Phone class with validation to ensure the phone number contains exactly 10 digits. Parent class is Field
    def __init__(self, value):
        if not value.isdigit() or len(value) != 10:
            raise ValueError("Phone number must consist of 10 digits.")
        super().__init__(value)

class Birthday(Field):
    # Birthday class with validation to ensure the date is in correct format. Data is stored in datetime format
    def __init__(self, value):
        try:
            birthday = datetime.strptime(value, "%d.%m.%Y").date()
            super().__init__(birthday)
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
    
    # since Birthday class is datetime format, it's better to add __str__ and __repr__ methods
    def __str__(self):
        return self.value.strftime("%d.%m.%Y")

    def __repr__(self):
        return self.value.strftime("%d.%m.%Y")

class Record:
    # This class holds a contact's information, including name and a list of phone numbers.
    def __init__(self, name):
        self.name = Name(name) # Name object, ensuring the name is validated.
        self.phones = [] # List to store multiple Phone objects.
        self.birthday = None # by defauld birthday field is empty

    def add_phone(self, phone):
        self.phones.append(Phone(phone))  # Adds a new Phone object after validation.

    def remove_phone(self, phone):
        # Attempts to remove a phone number from the list; if not found, does nothing.
        self.phones = [p for p in self.phones if p.value != phone]

    def edit_phone(self, old_phone, new_phone):
        # Edits an existing phone number; if not found, raises an error.
        try:
            # This will create a temporary Phone object and use it for comparison
            index = self.phones.index(Phone(old_phone))
            self.phones[index] = Phone(new_phone)
        except ValueError:
            raise ValueError("Old phone number not found.")

    def find_phone(self, phone):
        # Finds and returns a phone object; if not found, returns None.
        for p in self.phones:
            if p.value == phone:
                return p
        return None
    
    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    # adding birthday to str method in record
    def __str__(self):
        phones_str = '; '.join(p.value for p in self.phones)
        birthday_str = f", Birthday: {self.birthday}" if self.birthday else ""
        return f"Contact name: {self.name.value}, Phones: {phones_str}{birthday_str}"
    
    # defining the method to ensure correct serialization of Record values
    def __getstate__(self):
        return self.__dict__
    
    # defining the method to ensure correct deserialization of Record values   
    def __setstate__(self, state):
        self.__dict__.update(state)

# Since classe AddressBook inherit from UserDict, it will rely on the default serialization behavior of the dictionary. 
# __getstate__ and __setstate__ method don't need to be defined
class AddressBook(UserDict):
    # Manages a collection of Record objects, providing methods to manipulate them.
    def add_record(self, record: Record):
        if record.name.value in self.data:
            raise ValueError("Record with this name already exists.")
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]
        else:
            raise KeyError("Record not found.")
    
    def get_upcoming_birthdays(self, days=7):
        upcoming_birthdays = []
        today = date.today()
        for record in self.data.values():
            # if birthday is not indicated in the record, it will be skipped 
            if record.birthday:
                birthday_this_year = record.birthday.value.replace(year=today.year)
                # if birthday this year already passed we will consider date of birthday next year
                if birthday_this_year < today:
                    birthday_this_year = birthday_this_year.replace(year=today.year + 1)
                # if birthday is withing upcoming 7 (or other) days, record will be added to the list
                if 0 <= (birthday_this_year - today).days <= days:
                    # adjusting for weekend - if bithsay ison weekend, congratulation date is switched to the next Monday
                    if birthday_this_year.weekday() >= 5:
                        days_ahead = 7 - birthday_this_year.weekday() # for how many days we need to switch date of congratulation
                        congratulation_date = (birthday_this_year + timedelta(days=days_ahead)).strftime("%d.%m.%Y")
                    else:
                        congratulation_date = birthday_this_year.strftime("%d.%m.%Y")
                    upcoming_birthdays.append({"name": record.name.value, "congratulation date": congratulation_date})
        return upcoming_birthdays

    def __str__(self):
        return '\n'.join(str(record) for record in self.data.values())

def main():
    contact_book = load_data() # opening last condition of addressbook or creates empty Addressbook
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)
        if command in ["close", "exit"]:
            save_data(contact_book) # before closing the session contact_book condition is saved
            print("Good bye!")
            break
        elif command == "hello":
            print("How can I help you?")
        elif command == "add":
            print(add_contact(args, contact_book))
        elif command == "change":
            print(change_contact(args, contact_book))
        elif command == "phone":
            print(show_phone(args, contact_book))
        elif command == "all":
            print(show_all(contact_book))
        elif command == "add-birthday":
            print(add_birthday(args, contact_book))
        elif command == "show-birthday":
            print(show_birthday(args, contact_book))
        elif command == "birthdays":
            print(birthdays(contact_book))
        else:
            print("Invalid command.")
        
def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, args

def input_error_add(func): # decorator to work with Errors in add command
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e: 
            return str(e) # if phone is provided in wrong format
        except IndexError:
            return "Give me name and phone please." # if user didn't provide needed arguments with a command 
    return inner

@input_error_add
def add_contact(args: list, contact_book: AddressBook):
    phone = Phone(args[1]) # convirting to Phone format and checking if data is provided correctly
    name = args[0] # convirting to Name format
    if name in contact_book:
        record = contact_book.find(name)
        record.add_phone(phone.value)
        return "New phone added to contact"
    else:
        record = Record(name)
        record.add_phone(phone.value)
        contact_book.add_record(record)
        return "Contact added"

def input_error_change(func): # decorator to work with Errors in change command
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return str(e) 
        except IndexError:
            return "Give me name, old phone and new phone please." # if user didn't provide needed arguments with a command 
    return inner

@input_error_change
def change_contact(args: list, contact_book: AddressBook):
    name = args[0]
    old_phone = Phone(args[1])
    new_phone = Phone(args[2])
    if name in contact_book:
        record = contact_book.find(name)
        record.edit_phone(old_phone.value, new_phone.value)
        return "Number was edited"
    else:
        return f"There is no {name} in contact book."

def input_error_show(func): # decorator to work with Errors in phone command
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IndexError:
            return "Give me name please." # if user didn't provide needed arguments with a command 
    return inner

@input_error_show
def show_phone(args: list, contact_book: AddressBook):
    name = args[0]
    record = contact_book.find(name)
    if record:
        return record.phones
    else:
        return f"There is no {name} in contact book."

# in show_all function we don't need decorator, since typically no Errors are possible
def show_all(contact_book: AddressBook):
    if contact_book: 
        return contact_book
    else:
        return "Contact book is empty"

def input_error_add_birthday(func): # decorator to work with Errors in phone command
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IndexError:
            return "Give me name and birthday please." # if user didn't provide needed arguments with a command 
        except ValueError as e:
            return str(e)
    return inner

@input_error_add_birthday
def add_birthday(args: list, contact_book: AddressBook):
    name = args[0]
    birthday = Birthday(args[1])
    if name in contact_book:
        record = contact_book.find(name)
        record.add_birthday(birthday.value)
        return "Birthday added"
    else:
        return f"There is no {name} in contact book."

def input_error_show_birthday(func):
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IndexError:
            return "Give me name please."
    return inner

@input_error_show_birthday
def show_birthday(args, contact_book: AddressBook):
    name = args[0]
    if name in contact_book:
        record = contact_book.find(name)
        if record.birthday:
            return record.birthday
        else:
            return f"Birthday of {name} is not indicated in contact book"
    else:
        return f"There is no {name} in contact book."

def birthdays(contact_book: AddressBook):
    return contact_book.get_upcoming_birthdays()

# saves addressbook condition to the file
def save_data(book: AddressBook, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

# loads last condition of addressbook or creates an addressbook at the first session
def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()

if __name__ == "__main__":
    main()