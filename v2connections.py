import json
import sys
import questionary
from questionary import Style

blue_text = "\033[1;34m"
red_text = "\033[1;31m"
cyan_text = "\033[1;36m"
purp_text = "\033[1;35m"
green_text = "\033[1;32m"
default_text = "\033[1;0m"

data_saved_message = f"\n\n{purp_text}************************\n{green_text}Data saved successfully.\n{purp_text}************************\n"

def save_data(data, filename):
    try:
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)
            print(data_saved_message)
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)

def load_data(filename):
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print("The file was not found. Please check the file path.")
        return None


def list_data(data):
    companies = [company for company in data if company != 'exclusions']
    answer = questionary.select(
        "Choose a company to query from the following list:",
        choices=companies,
        style=custom_style  
    ).ask()

    if answer in companies:
        print(f"\nHere are the available connections for the company {green_text}{answer}{default_text},\nfollowed by their respective level of familiarity:\n")
        for person, level in data[answer]["mom"].items():
            print(f"{default_text}{person.title()}: {cyan_text}{level}")
    else:
        print("\nThe company name entered is not in the list. Please try again.")


def search_data(data):
    query = input("\nEnter a name or familiarity level to search for: ")
    result = {}
    if query.isdigit():
        query_level = int(query)
        for company, details in data.items():
            # Check if 'mom' exists and is a dictionary
            if 'mom' in details and isinstance(details['mom'], dict):
                matching_entries = {name: level for name, level in details['mom'].items() if level == query_level}
                if matching_entries:
                    result[company] = matching_entries
    else:  # Search by name
        query_name = query.lower()
        for company, details in data.items():
            # Check if 'mom' exists and is a dictionary
            if 'mom' in details and isinstance(details['mom'], dict):
                matching_entries = {name: level for name, level in details['mom'].items() if name.lower() == query_name}
                if matching_entries:
                    result[company] = matching_entries

    if result:
        for company, names in result.items():
            print("\n" + f"{purp_text}-"*50 + f"\n  {green_text}{company.title()}:\n")
            for name, level in names.items():
                print(f"    {default_text}{name.title()}: {cyan_text}{level}")
    else:
        print(f"\nNo results found for {query}.")


def add_entries(data):
    while True:
        company_name = input(f"\nEnter a new company name or type '{red_text}exit{default_text}' to finish: ")
        if company_name.lower() == 'exit':
            break
        if company_name not in data:
            data[company_name] = {'mom': {}}
        
        while True:
            person_name = input(f"\nAdd a person to this company or type '{red_text}done{default_text}' to add another company: ")
            if person_name.lower() == 'done':
                break
            
            # Check if the person is in the exclusions list
            if person_name.lower() in (name.lower() for name in data.get('exclusions', {}).get('mom', [])):
                print("This person is in the exclusions list, skipping addition.")
                continue
            
            # Find any existing entry of this person to get the familiarity level
            existing_level = None
            for details in data.values():
                if 'mom' in details and person_name.lower() in (name.lower() for name in details['mom']):
                    existing_level = details['mom'][next(name for name in details['mom'] if name.lower() == person_name.lower())]
                    break
            
            if existing_level is not None:
                print(f"\n{person_name} exists elsewhere, setting familiarity level to {cyan_text}{existing_level}{default_text}.")
                data[company_name]['mom'][person_name] = existing_level
            else:
                # No existing level found, so set value to None
                data[company_name]['mom'][person_name] = None


def update_familiarity(data):
    updated_names = {}  # Dictionary to keep track of updated names and their assigned levels or exclusions

    # Iterate over each company (excluding 'exclusions') and person to update or exclude them
    for company, details in data.items():
        if company != 'exclusions' and 'mom' in details:  # Skip 'exclusions' and check if 'mom' exists
            for name in list(details['mom'].keys()):
                if name not in updated_names and details['mom'][name] is None:  # Check if not already updated or excluded
                    new_level = input(f"\nSet familiarity level for {green_text}{name}{default_text} or type '{red_text}exclude{default_text}' to move to exclusions: ")

                    if new_level.lower() == 'exclude':
                        if name not in data['exclusions']['mom']:
                            data['exclusions']['mom'].append(name)

                        # Remember this name as excluded
                        updated_names[name] = 'exclude'
                        print(f"\n{name.title()} excluded.")
                    else:
                        # Update all occurrences with the new level
                        updated_names[name] = int(new_level)
                        print(f"\nFamiliarity level {cyan_text}{new_level}{default_text} assigned to {name.title()}.")

    # Apply the updates or exclusions across all companies (again, excluding 'exclusions')
    for company, details in data.items():
        if company != 'exclusions' and 'mom' in details:
            for name in list(details['mom'].keys()):
                if name in updated_names:
                    if updated_names[name] == 'exclude':
                        # Remove excluded names from companies but not from exclusions
                        del details['mom'][name]
                        print(f"\nAll other instances of {name.title()} succsessfully excluded.")
                    else:
                        # Update the familiarity level for names not excluded
                        details['mom'][name] = updated_names[name]
                        print(f"\n{name.title()} successfully updated with new familiarity level.")



custom_style = Style([
    ('qmark', 'fg:purple bold underline'),   # token in front of the question
    ('question', 'fg:purple bold underline'),  # Style for the question
    ('pointer', 'fg:purple bold'),  # Style for the pointer
    ('highlighted', 'fg:green bold') # pointed-at choice in select and checkbox prompts
])


def main_menu():
    print("\n" + f"{purp_text}-"*50 + "\n")
    response = questionary.select(
        "What would you like to do ?",
        choices=[
            "List all connections for a specific company",
            "Search for a specific person or a familiarity level between 1 and 3",
            "Add new companies and connections",
            "Assign familiarity levels to newly added connections",
            "Exit"
        ],
        style=custom_style
    ).ask()
    return response


def main():
    data = load_data("db.json")
    if data is None:
        return

    while True:
        choice = main_menu()
        
        if choice == "List all connections for a specific company":
            list_data(data)
        elif choice == "Search for a specific person or a familiarity level between 1 and 3":
            search_data(data)
        elif choice == "Add new companies and connections":
            add_entries(data)
            save_data(data, "db.json")
        elif choice == "Assign familiarity levels to newly added connections":
            update_familiarity(data)
            save_data(data, "db.json")
        elif choice == "Exit":
            print("Exiting...")
            break

if __name__ == '__main__':
    main()