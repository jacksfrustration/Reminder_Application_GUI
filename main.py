import csv
from datetime import datetime, timedelta
import pandas as pd
from tkinter import *
from tkinter import simpledialog, messagebox
from twilio.rest import Client
import smtplib
import kickbox


class Reminder:
    MY_EMAIL = "thechurchcomms@gmail.com"
    PASSWORD = "***************"
    ACCOUNT_SID = '**************'
    AUTH_TOKEN = '****************'
    TWILIO_NUMBER = '+447700162356'
    DATE_FORMAT = "%d-%m-%Y"
    CSV_FILE = "data.csv"
    API_KEY = "****************"


    def __init__(self, window, canvas, bg_pic, sms_pic, email_pic, save_pic, search_pic, delete_pic, clear_all_pic, view_all_pic):
        self.window = window
        self.canvas = canvas
        self.bg_pic = bg_pic
        self.sms_pic = sms_pic
        self.email_pic = email_pic
        self.save_pic = save_pic
        self.search_pic = search_pic
        self.delete_pic = delete_pic
        self.clear_all_pic = clear_all_pic
        self.view_all_pic = view_all_pic
        self.dates_list_starting_from_today = self.generate_dates_list()
        self.create_gui()

    def verify_email(self,email):
        '''verifies and returns true if the email address provided exists'''
        client=kickbox.Client(self.API_KEY)
        kbx=client.kickbox()
        response=kbx.verify(email)
        return response.body['result']!="undeliverable"

    def clear_widget_entries(self):
        '''clear all entry information to reset after the user
        is done with his input'''
        self.send_date_ent.delete(0, END)
        self.name_ent.delete(0, END)
        self.description_ent.delete(0, END)
        self.phone_ent.delete(0, END)
        self.email_ent.delete(0, END)
        self.end_date_ent.delete(0, END)

    def show_all(self):
        '''generates a messagebox window that includes all of the information about all of the saved reminders'''
        message_body = ""
        saved_data = self.read_csv_file(self.CSV_FILE)
        if not saved_data:
            self.show_error(title="No Reminders", message="You have no saved reminders! Please add some reminders.")
            return

        for ent in saved_data:
            final_email_address = ent["email address"].replace('"', '').replace('[', '').replace(']', '').replace("'", "") if ent["have email address"] else "not provided"
            message_body += (
                    f"\nOn {ent['send date']}, {ent['name']} will be reminded to {ent['description']}\n"
                    f"Their phone number is {ent['phone number']}\n"
                    f"Their email address is {final_email_address}\n"
                )

        messagebox.showinfo(title="Found Reminders", message=message_body)

    def delete_all(self):
        """Delete all reminders by reinitializing the CSV file."""
        with open(self.CSV_FILE, "w") as file:
            writer = csv.writer(file)
            writer.writerow(["name", "send date", "description", "phone number", "email address", "recurring", "have email address"])

    def generate_dates_list(self):
        '''generates a list of dates in order to correctly validate future send or end dates set by the user'''
        return [(datetime.now() + timedelta(days=i)).strftime(self.DATE_FORMAT) for i in range(100000)]

    def check_date(self, date_str):
        ''''checks if the date passed in is in the previously generated
        list of dates and if the assignment date is at least one day behind the send date'''
        if not bool(date_str):
            self.show_error(title="Error", message="You have not entered a date. Please try again!")
            return
        if date_str not in self.dates_list_starting_from_today:
            self.show_error(title="OOOOOOOOPS",message=f"The date you entered is not available!!\n"
                                                            f"Please enter a date between {self.dates_list_starting_from_today[0]} - {self.dates_list_starting_from_today[-1]}")
            return
        try:
            date = datetime.strptime(date_str, self.DATE_FORMAT)
            if date >= datetime.now():
                return True
            else:
                self.show_error(title="Error", message="The date you entered is in the past. Please enter a future date.")
        except ValueError:
            self.show_error(title="Error", message="The date format is incorrect. Please enter a date in DD-MM-YYYY format.")
            return

    def check_alphabetical(self, stg):
        '''checks if only alphabetical characters are passed in to the name and description entries'''
        return bool(stg) and all(x.isalpha() or x.isspace() or x.isdigit() for x in stg)

    def send_email(self, to_email, subject, body):
        '''sends email'''
        try:
            with smtplib.SMTP("smtp.gmail.com") as connection:
                connection.starttls()
                connection.login(user=self.MY_EMAIL, password=self.PASSWORD)
                connection.sendmail(from_addr=self.MY_EMAIL, to_addrs=to_email, msg=f"Subject:{subject}\n\n{body}")
        except Exception as e:
            self.show_error(title="OOOOOOOOps",message=f"An error occurred. {e}")

    def send_sms(self, to_number, body):
        '''sends the sms '''
        try:
            client = Client(self.ACCOUNT_SID, self.AUTH_TOKEN)
            client.messages.create(body=body, from_=self.TWILIO_NUMBER, to=to_number)
        except Exception as e:
            self.show_error(title="OOOOOOOOps",message=f"An error occurred: {e}")

    def read_csv_file(self, file_name):
        '''read csv file and if not available create it and enter the headers'''
        try:
            return pd.read_csv(file_name).to_dict("records")
        except FileNotFoundError:
            with open(file_name, "w") as file:
                writer = csv.writer(file)
                writer.writerow(["name", "send date", "description", "phone number", "email address", "recurring", "have email address"])
            return []

    def save_csv_file(self, file_name, data):
        '''save csv file entry'''
        pd.DataFrame(data).to_csv(file_name, index=False)

    def save_info(self):
        saved_data = self.read_csv_file(self.CSV_FILE)
        send_date = self.send_date_ent.get()

        if not self.check_date(send_date):
            return

        name = self.name_ent.get().title()
        desc = self.description_ent.get()
        phone_number = self.phone_ent.get()

        if len(phone_number) != 11 or not phone_number.isdigit():
            self.show_error(title="Error",
                                 message="Invalid phone number. Please enter a valid 11-digit UK phone number starting with 0.")
            return

        if not self.check_alphabetical(name) or not self.check_alphabetical(desc):
            self.show_error(title="Error",
                                 message="Name or task description contains invalid characters. Please enter only alphabetical characters and spaces.")
            return

        have_email_address = self.var2.get() == 1
        to_email_address = self.email_ent.get() if have_email_address else " not provided"
        if have_email_address and not self.verify_email(to_email_address):
            self.show_error(title="Invalid Email",
                                 message="The email address you entered does not exist. Please enter a valid email address.")
            return

        recurring = self.var1.get() == 1
        end_date = self.end_date_ent.get() if recurring else ""

        if recurring and not self.check_date(end_date):
            self.show_error(title="OOOOOOps",message="End date is not in the right format,\nPlease enter a date in DD-MM-YYYY format!!")
            return

        self.process_save_info(saved_data, name, send_date, desc, phone_number, to_email_address, have_email_address,
                               end_date, recurring)

    def process_save_info(self, saved_data, name, send_date, desc, phone_number, to_email_address, have_email_address, end_date, recurring):
        '''this function is meant to aid the save info function
        if the reminder is recurring then the list of send dates is generated.
        if an email address is provided then it is saved along with all the other information
        as long as the user presses yes on the prompt.'''
        if recurring:
            frequency = simpledialog.askinteger(title="Task Frequency", prompt="How many days should the task occur?")
            start_date_index = self.dates_list_starting_from_today.index(send_date)
            end_date_index = self.dates_list_starting_from_today.index(end_date)
            send_dates = self.dates_list_starting_from_today[start_date_index:end_date_index:frequency]
        else:
            send_dates = send_date

        entry = {
            "name": name, "send date": send_dates, "description": desc, "phone number": phone_number,
            "email address": to_email_address, "recurring": recurring, "have email address": have_email_address
        }
        if messagebox.askyesno(title="Save Information", message=f"{name}? will be reminded to {desc} on {send_dates}\n"
                                                                 f"Their phone number is {phone_number}\n"
                                                                 f"Their email address is {to_email_address}"):
            saved_data.append(entry)
            self.save_csv_file(self.CSV_FILE, saved_data)
            self.clear_widget_entries()
            messagebox.showinfo(title="Congratulations!!!!",message="Way to go!!\nYou have successfully saved this reminder!\n")


    def get_due_date(self):
        return (datetime.now() + timedelta(days=7)).strftime("%d-%m-%Y")


    def reminder_func(self,send_method):
        todays_date = datetime.now().strftime(self.DATE_FORMAT)
        data = self.read_csv_file(self.CSV_FILE)
        search_results = [entry for entry in data if todays_date in entry["send date"]]

        if not search_results:
            self.show_error(title="OOOOOOPS", message="I have not found any reminders to send")
            return
        for result in search_results:
            msg=f"Dear {result['name']} on {self.get_due_date()} you will have to {result['description']}"

            if send_method=="SMS":
                if str(result["phone number"]).startswith("0"):
                    final_phone_number="+44"+str(result["phone number"])[1:]
                else:
                    final_phone_number="+44"+str(result["phone number"])
                    if messagebox.askyesno(title=f"Send {send_method}",
                                           message=f"Would you like to remind {result['name']} that on {self.get_due_date()} "
                                                   f"they will have to {result['description']}\n"
                                                   f"Their phone number is {result['phone number']}"):
                        self.send_sms(final_phone_number,msg)
            else:
                if result["have email address"]:
                    msg = f"Dear {result['name']} on {self.get_due_date()} you will have to {result['description']}"
                    final_email_address = result["email address"].replace("'", "").replace("[", "").replace("]", "")

                    if messagebox.askyesno(title=f"Send {send_method}",message=f"Would you like to remind {result['name']} that on {self.get_due_date()} they will have to {result['description']}\n"
                                                                       f"Their email address is {final_email_address}"):
                        self.send_email(final_email_address, subject="Reminder", body=msg)



    def search_info(self):
        try:
            search_parameter = simpledialog.askstring("Search Parameter", "Enter search parameter (name, phone number, email address):").lower()
            search_term = simpledialog.askstring("Search Value", "Enter search value:").lower()
        except AttributeError:
            self.show_error(title="OOOOOOOPS",message="You have not entered parameter or search term!!")
            return
        else:
            if search_parameter not in ("name", "phone number", "email address"):
                self.show_error("Error", "Invalid search parameter. Please enter name, phone number, or email address.")
                return
            search_results=[]
            data = self.read_csv_file(self.CSV_FILE)
            if search_parameter.lower()=="phone number":
                for ent in data:
                    if str(ent["phone number"]).startswith("0"):
                        if ent["phone number"]==search_term:
                            search_results.append(ent)
                    else:
                        if "0"+str(ent["phone number"])==search_term:
                            search_results.append(ent)
            elif search_parameter.lower()=="email address":
                search_results=[entry for entry in data if entry[search_parameter]==search_term]
            else:
                search_results = [entry for entry in data if entry[search_parameter].lower() == search_term]

            if search_results:
                for result in search_results:
                    email_address = result["email address"].replace("'", "").replace("[", "").replace("]", "") if result["have email address"] else "not provided"
                    messagebox.showinfo(
                        title="Search Results",
                        message=(
                            f"Reminder found for {result['name']}:\n"
                            f"Description: {result['description']}\n"
                            f"Send Date(s): {result['send date']}\n"
                            f"Phone Number: {result['phone number']}\n"
                            f"Email Address: {email_address}"
                        )
                    )
            else:
                messagebox.showinfo(title="Search Results", message="No matching reminders found.")


    def delete_info(self):
        try:
            search_parameter = simpledialog.askstring("Delete Reminder",
                                                  "By which parameter do you want to find the reminder?\nYour options are name, phone number, or email address").lower()
        except AttributeError:
            self.show_error(title="OOOOOPS",message="You have not entered a parameter to complete the search!!")
            return
        else:
            if search_parameter not in ("name", "phone number", "email address"):
                self.show_error("Error", "You have not entered a correct search parameter!\nPlease try again.")
                return
            try:
                search_term = simpledialog.askstring("Delete Reminder", f"Please enter a {search_parameter} to search for:").lower()
            except AttributeError:
                self.show_error(title="OOOOOOPS",message="You have not entered a search term!!\n")
            else:
                data = self.read_csv_file("data.csv")

                for ent in data:
                    if search_parameter.lower()=="phone number":
                        if str(ent["phone number"]).startswith("0"):
                            if ent["phone number"] == search_term:
                                self.delete_entry(data,ent)

                        else:
                            if "0" + str(ent["phone number"]) == search_term:
                                self.delete_entry(data,ent)
                    elif search_parameter.lower()=="name":

                        if ent[search_parameter].lower()==search_term.lower():
                            self.delete_entry(data,ent)

                    else:
                        if ent["email address"]==search_term:
                            self.delete_entry(data,ent)






    def delete_entry(self,data,ent):
        final_email_address=ent["email address"].replace("'","").replace("[","").replace("]","") if ent["have email address"] else "not provided"

        if messagebox.askyesno(title="Found reminders",
                               message=f"On {ent['send date']} {ent['name']} will be reminded to {ent['description']}\n"
                                       f"Their phone number is {ent['phone number']}\n"
                                       f"Their email address is {final_email_address}\n"
                                       f"Would you like to delete this entry?\n"):
            data.remove(ent)
            self.save_csv_file("data.csv", data)
            messagebox.showinfo(title="Success", message="Reminder(s) deleted successfully.")
    def show_error(self,title,message):
        messagebox.showerror(title=title,message=message)

    def create_gui(self):
        self.window.title("Reminder Application")
        self.window.geometry("1080x720")
        canvas.create_image(380, 240, image=self.bg_pic)

        Label(self.window, text="Send Date in DD-MM-YYYY: ", fg="blue").grid(row=1, column=0)
        self.send_date_ent = Entry(self.window)
        self.send_date_ent.grid(row=1, column=1)

        Label(self.window, text="End Date in DD-MM-YYYY format:", fg="blue").grid(row=1, column=2)
        self.end_date_ent = Entry()
        self.end_date_ent.grid(row=1, column=3)
        Label(self.window, text="Task: ", fg="blue").grid(row=1, column=4)
        self.description_ent = Entry(self.window)
        self.description_ent.grid(row=1, column=5)
        self.var2 = IntVar()
        Checkbutton(self.window, variable=self.var2, text="Do they have email address", onvalue=1, offvalue=0,fg="blue").grid(row=1, column=6)
        self.var1 = IntVar()
        Checkbutton(self.window, text="Recurring", variable=self.var1, onvalue=1, offvalue=0, fg="blue").grid(row=2,column=0)

        Label(self.window, text="Full Name: ", fg="blue").grid(row=2, column=1)

        Label(self.window, text="Phone Number: ", fg="blue").grid(row=2, column=3)

        self.name_ent = Entry(self.window)
        self.name_ent.grid(row=2, column=2, columnspan=1)

        self.phone_ent = Entry(self.window)
        self.phone_ent.grid(row=2, column=4)
        Label(self.window, text="Email address: ", fg="blue").grid(row=2, column=5)
        self.email_ent = Entry()
        self.email_ent.grid(row=2, column=6, columnspan=2)

        Button(self.window, text="Save Information", compound=BOTTOM, command=self.save_info, fg="#ca11ef",image=self.save_pic).grid(row=3, column=0, columnspan=1)
        Button(self.window, text="Show All Reminders", compound=BOTTOM, image=self.view_all_pic, command=self.show_all,fg="#ca11ef").grid(row=3, column=1)

        Button(self.window, text="Search Reminders", command=self.search_info, compound=BOTTOM, fg="#ca11ef",image=self.search_pic).grid(row=3, column=2, columnspan=2)

        Button(self.window, text="Delete Specific Reminder", command=self.delete_info, compound=BOTTOM, fg="#ca11ef",image=self.delete_pic).grid(row=3, column=4, columnspan=2)
        Button(self.window, text="Clear All Reminders", command=self.delete_all, compound=BOTTOM, fg="#ca11ef",image=self.clear_all_pic).grid(row=3, column=6, columnspan=2)
        Button(self.window, text="Send SMS", image=self.sms_pic, command= lambda: self.reminder_func("SMS"), compound=BOTTOM,fg="#ca11ef").grid(row=4, column=1, columnspan=2)
        Button(self.window, compound=BOTTOM, image=self.email_pic, text="Send Emails", command=lambda: self.reminder_func("EMAIL"),fg="#ca11ef").grid(row=4, column=3, columnspan=2)



if __name__ == "__main__":
    root = Tk()
    canvas = Canvas(root, width=768, height=483)
    canvas.grid(row=0, column=1, columnspan=8)

    bg_pic = PhotoImage(file="church_pic.png")
    sms_pic = PhotoImage(file="./sms.png")
    email_pic = PhotoImage(file="./email.png")
    save_pic = PhotoImage(file="./save_button.png")
    search_pic = PhotoImage(file="./search_button.png")
    delete_pic = PhotoImage(file="./delete_button.png")
    clear_all_pic = PhotoImage(file="clear_all.png")
    view_all_pic = PhotoImage(file="view_all.png")

    reminder_app = Reminder(root, canvas, bg_pic, sms_pic, email_pic, save_pic, search_pic, delete_pic, clear_all_pic, view_all_pic)
    root.mainloop()