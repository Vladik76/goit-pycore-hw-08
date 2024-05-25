from collections import UserDict
from datetime import date,datetime,timedelta
import re
import pickle

#Error Handlers

class PhoneValidationError(Exception):
     """
     Custom exception. Phone validation
     """
     def __init__(self, message="Phone should contain 10 numbers."):
        self.message = message
        super().__init__(self.message)

class NotUniquePhoneError(Exception):
    """
    Error when phone is not unique
    """
    def __init__(self, message="The phone number already exists"):
        self.message = message
        super().__init__(self.message)

class ContactNotFound(Exception):
    """
    Error when contact not found
    """
    def __init__(self, message="Contact not found"):
        self.message = message
        super().__init__(self.message)


# Fields
class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)
    
    def value(self):
        return self.value

        

class Name(Field):
	pass

class Phone(Field):
    def __init__(self, value):
        if not self.verify_phone(value):
            raise PhoneValidationError()
        super().__init__(value)

    def verify_phone(self,phone_number)->bool:
        pattern = r"^[0-9]{10}$"
        return re.match(pattern,phone_number) is not None

class Birthday(Field):
    def __init__(self, value):
        try:
            birthday=datetime.strptime(value, "%d.%m.%Y").date()
            super().__init__(birthday)
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

    def value(self):
        return super().value()
        
    def __str__(self):
        return super().value().strftime("%d.%m.%Y")
        

#Objects    
class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def find_phone(self,phone_number:str)->Phone:

        for p in self.phones:
            if p.value == phone_number:
                return p
    
    def check_duplicate(self,phone_number:str)->Phone:
        """
        Checks if passed phone number already in list of Phones
        Returns Phone if phone_number does not exists otherwise raise exception NotUniquePhoneError
        """
        phone=Phone(phone_number)

        if phone in self.phones:
            raise NotUniquePhoneError
        else:
            return phone

    def add_phone(self,phone_number:str)->str:
        """
        Add phone

        Function raises: 
        PhoneValidationError exception if new phone number is incorrect
        NotUniquePhoneError exception if new phone already in list of phones
        """
        self.phones.append(self.check_duplicate(phone_number)) # append to phones list if correct. Oterwise, raise an Exception

    def edit_phone(self,old_phone_number:str,new_phone_number:str)->None:
        """
        Edit phone

        Function raises: 
        ValueError exception if phone is not in list
        PhoneValidationError exception if new phone number is incorrect
        NotUniquePhoneError exception if new phone already in list of phones
        """
        old_phone = self.find_phone(old_phone_number)
        if old_phone:
            self.phones[self.phones.index(old_phone)] = self.check_duplicate(new_phone_number)
        else:
            raise ValueError(f"Phone {old_phone_number} not found")

    def remove_phone(self,phone_number:str)->None:
        """
        Remove phone from the list of phones

        Function raises: 
        ValueError exception if phone is not in list
        PhoneValidationError exception if new phone number is incorrect
        """
        self.phones.remove(self.find_phone(phone_number))
    
    def show_phones(self):
        return ", ".join( str(phone) for phone in self.phones)
        
    
    def add_birthday(self,date_of_birth:str)->str:
        """
        Add birthday

        Function raises: 
        ValueError - wrong DOB format
        """
        self.birthday = Birthday(date_of_birth)
    

    def __str__(self):
        return f"Contact name: {self.name.value}, Date of birth:{str(self.birthday)}, Phones: {'; '.join(p.value for p in self.phones)}"
    


class AddressBook(UserDict):
    
    def add_record(self,record:Record)->None:
        """
        Add Record to Address book
        Raises ValueError exception if record already exists.
        """
        if record.name.value not in self.data.keys():
            self.data[record.name.value] = record
        else:
            raise ValueError(f"The Record {record.name} already exists.")
        
    
    def find(self,name:str)->Record:
         return self.data.get(name,None)

    def delete(self,name:str)->None:
        """
        Raises KeyError if record does not exist
        """
        del self.data[name]
    
    def find_next_weekday(self,start_date, weekday):
        days_ahead = weekday - start_date.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return start_date + timedelta(days=days_ahead)


    def adjust_for_weekend(self,birthday):
        if birthday.weekday() >= 5:
            return self.find_next_weekday(birthday, 0)
        return birthday
    
    def date_to_string(self,date):
        return date.strftime("%d.%m.%Y")

    def get_upcoming_birthdays(self, days=7):
        upcoming_birthdays = []
        today = date.today()
        for contact in self.data.items():
            name,contact_data = contact  #unpack tuple
            if contact_data.birthday:
                birthday_this_year = contact_data.birthday.value.replace(year=today.year)
                if birthday_this_year < today:
                    birthday_this_year=birthday_this_year.replace(year=today.year+1)

                if 0 <= (birthday_this_year - today).days <= days:
                    birthday_this_year=self.adjust_for_weekend(birthday_this_year)
                    congratulation_date_str = self.date_to_string(birthday_this_year)
                    upcoming_birthdays.append(f"{name} has congratulation date on {congratulation_date_str}")
        return upcoming_birthdays

    def show_all_contacts(self):
        
        contacts=[]
        for contact in self.data.items():
            name,contact_data = contact  #unpack tuple
            contacts.append(str(contact_data))
        
        return contacts

# Business Logic

def input_error(func):
    """
    Decorator. Errors handler
    """

    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except NotUniquePhoneError as exc:
            return exc.message
        except PhoneValidationError as exc:
            return exc.message
        except ValueError as exc:
            return "Invalid parameters. " + str(exc)
        except KeyError as exc:
            return "Invalid parameters. " + str(exc)
        except ContactNotFound as exc:
            return exc.message

    return inner

def parse_input(user_input):
    """
    This function parses usder input and return command and list of the arguments
    """
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args

    
@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message

@input_error
def change_contact(args,book: AddressBook):
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if record is None:
        raise ContactNotFound(f"Record {name} not found.")
    else:
        record.edit_phone(old_phone,new_phone)
        return "Phone updated."

@input_error
def show_phones(args,book:AddressBook):
    name,*_ = args
    record = book.find(name)
    if record is None:
        raise ContactNotFound(f"Record {name} not found.")
    else:
        return f"Phones for {name}:\n{record.show_phones()}"

def show_all_contacts(book:AddressBook):
     return "\n".join(book.show_all_contacts())

@input_error
def add_birthday(args,book:AddressBook):
    name, birthday, *_ = args
    record = book.find(name)
    if record is None:
        raise ContactNotFound(f"Record {name} not found.")
    else:
        record.add_birthday(birthday)
        return f"The birthday for the contact {name} was set to {birthday}"

@input_error
def show_birthday(args,book:AddressBook):
    name, *_ = args
    record = book.find(name)
    if record is None:
        raise ContactNotFound(f"Record {name} not found.")
    else:
        return f"The birthday for the contact {name} is {str(record.birthday)}"        

def show_birthdays(book:AddressBook):
    return "\n".join(book.get_upcoming_birthdays())


def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook() 

    
#User Interface

def main():
    book = load_data()
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Good bye!")
            save_data(book)
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args,book))

        elif command == "phone":
            print(show_phones(args,book))

        elif command == "all":
            print(show_all_contacts(book))

        elif command == "add-birthday":
            print(add_birthday(args,book))

        elif command == "show-birthday":
            print(show_birthday(args,book))

        elif command == "birthdays":
            print(show_birthdays(book))

        else:
            print("Invalid command.")



if __name__ == "__main__":
   main()