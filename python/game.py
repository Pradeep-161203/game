import tkinter as tk
from tkinter import messagebox, simpledialog
import random
import nltk
from nltk.corpus import wordnet as wn
import mysql.connector

# Download required nltk data
nltk.download('wordnet')


class Database:
    def __init__(self):
        self.conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # Add your MySQL password
            database="user_db"
        )
        self.cursor = self.conn.cursor()
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL
            )"""
        )
        self.conn.commit()

    def add_user(self, username, password):
        try:
            self.cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            self.conn.commit()
            return True
        except mysql.connector.Error as e:
            print(e)
            return False

    def validate_user(self, username, password):
        self.cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        return self.cursor.fetchone() is not None


class WordGuessingGame:
    def __init__(self, root, main_root, difficulty, db):
        self.root = root
        self.main_root = main_root  # Reference to main window
        self.difficulty = difficulty  # Set difficulty level
        self.db = db
        self.word_clue_dict = self.generate_word_list_by_difficulty()

        self.root.title("Word Guessing Game")
        self.root.geometry("600x400")  # Set window size
        self.root.configure(bg="#f0f8ff")  # Light blue background

        # Set word length limits based on difficulty
        if difficulty == "Easy":
            self.word_length_range = (3, 5)
        elif difficulty == "Medium":
            self.word_length_range = (6, 8)
        else:  # Hard
            self.word_length_range = (9, 12)

        # Initialize game variables
        self.word_to_guess, self.clue = self.get_random_word()
        if not self.word_to_guess:
            return  # Exit if no valid words were found
        self.guessed_word = ["_"] * len(self.word_to_guess)
        self.guessed_letters = []
        self.wrong_guesses = 0
        self.max_wrong_guesses = 6  # Hangman-like mechanic
        self.points = 100  # Initial points
        self.total_points = 0  # Cumulative points across levels
        self.hint_used = False
        self.hint_index = 0  # To track how many hints have been given
        self.level = 1  # Level counter

        # Main Layout
        self.setup_layout()

        # Display word to guess (with underscores)
        self.update_display()

    def generate_word_list_by_difficulty(self):
        """Generates word lists categorized by difficulty."""
        word_clue_dict = {}
        
        # Get a list of words from WordNet
        words = list(wn.words())
        
        # Categorize them into easy, medium, and hard based on word length
        for word in words:
            if word.isalpha():  # Filter out words with numbers or special characters
                definition = self.get_definition(word)
                if len(word) >= 3 and len(word) <= 5:
                    word_clue_dict[word] = definition
                elif len(word) >= 6 and len(word) <= 8:
                    word_clue_dict[word] = definition
                elif len(word) >= 9:
                    word_clue_dict[word] = definition
        return word_clue_dict

    def get_definition(self, word):
        """Gets the definition of a word from WordNet."""
        synsets = wn.synsets(word)
        if synsets:
            return synsets[0].definition()
        return "No definition available"

    def get_random_word(self):
        """Get a random word and its clue from the dictionary."""
        valid_words = [word for word in self.word_clue_dict if self.word_length_range[0] <= len(word) <= self.word_length_range[1]]
        if not valid_words:
            messagebox.showerror("No Words", f"No words available for the selected difficulty ({self.difficulty}).")
            self.root.destroy()
            self.main_root.deiconify()  # Show the main menu
            return None, None
        word = random.choice(valid_words)
        return word, self.word_clue_dict[word]

    def setup_layout(self):
        # Title
        title = tk.Label(self.root, text="Word Guessing Game", font=("Arial", 24, "bold"), bg="#f0f8ff", fg="#4682b4")
        title.pack(pady=10)

        # Level label
        self.level_label = tk.Label(self.root, text=f"Level: {self.level}", font=("Arial", 16), bg="#f0f8ff", fg="#4682b4")
        self.level_label.pack(pady=10)

        # Display for the word
        self.word_label = tk.Label(self.root, text=" ".join(self.guessed_word), font=("Arial", 28), bg="#f0f8ff", fg="#2e8b57")
        self.word_label.pack(pady=10)

        # Input for guessing a letter
        self.letter_entry = tk.Entry(self.root, font=("Arial", 16), bg="#ffffff", fg="#000000")
        self.letter_entry.pack(pady=10)

        # Buttons with hover effects
        self.guess_button = self.create_button("Guess", self.guess_letter)
        self.guess_button.pack(pady=5)

        self.guess_word_button = self.create_button("Guess Word", self.guess_word)
        self.guess_word_button.pack(pady=5)

        self.hint_button = self.create_button("Get Hint", self.show_hint)
        self.hint_button.pack(pady=5)

        # Status label (for wrong guesses and game status)
        self.status_label = tk.Label(self.root, text=f"Wrong guesses: {self.wrong_guesses}/{self.max_wrong_guesses}", font=("Arial", 14), bg="#f0f8ff", fg="#4682b4")
        self.status_label.pack(pady=10)

        # Points label
        self.points_label = tk.Label(self.root, text=f"Points: {self.points}", font=("Arial", 14), bg="#f0f8ff", fg="#4682b4")
        self.points_label.pack(pady=10)

        # Back to Home button
        self.back_button = self.create_button("Back to Home", self.back_to_home, "#ff4500")
        self.back_button.pack(pady=5)

        # Reset button
        self.reset_button = self.create_button("Reset", self.reset_game, "#ff4500")
        self.reset_button.pack(pady=5)

    def create_button(self, text, command, bg_color="#4682b4"):
        button = tk.Button(self.root, text=text, command=command, bg=bg_color, fg="#ffffff", font=("Arial", 14))
        button.bind("<Enter>", lambda e: button.config(bg="#5bc0de"))
        button.bind("<Leave>", lambda e: button.config(bg=bg_color))
        button.config(pady=10, padx=20)
        return button

    def guess_letter(self):
        letter = self.letter_entry.get().lower()
        self.letter_entry.delete(0, tk.END)

        if len(letter) != 1 or not letter.isalpha():
            messagebox.showwarning("Invalid Input", "Please enter a single letter.")
            return

        if letter in self.guessed_letters:
            messagebox.showinfo("Already Guessed", f"You've already guessed '{letter}'. Try a different letter.")
            return

        self.guessed_letters.append(letter)

        if letter in self.word_to_guess:
            for i, char in enumerate(self.word_to_guess):
                if char == letter:
                    self.guessed_word[i] = letter
            self.update_display()
            self.points += 10  # Gain points for a correct guess
        else:
            self.wrong_guesses += 1
            self.points -= 5  # Lose points for a wrong guess
            self.update_status()

        self.update_points()

        # Check if the player won (guessed the word)
        if "_" not in self.guessed_word:
            self.end_game(win=True)

        # Check if the player has lost (too many wrong guesses)
        if self.wrong_guesses >= self.max_wrong_guesses:
            self.end_game(win=False)

    def guess_word(self):
        guessed_word = self.letter_entry.get().lower()
        self.letter_entry.delete(0, tk.END)

        if guessed_word == self.word_to_guess:
            self.end_game(win=True)
        else:
            messagebox.showwarning("Incorrect Guess", f"'{guessed_word}' is not the correct word.")
            self.wrong_guesses += 1
            self.points -= 10  # Lose points for an incorrect word guess
            self.update_status()
            self.update_points()

            # Check if the player has lost (too many wrong guesses)
            if self.wrong_guesses >= self.max_wrong_guesses:
                self.end_game(win=False)

    def show_hint(self):
            """Show the definition of the word as a hint."""
            if not self.hint_used:
                hint_definition = self.clue  # The clue now holds the definition
                messagebox.showinfo("Hint", f"Here's a hint: {hint_definition}")
                self.hint_used = True  # Mark hint as used
            else:
                messagebox.showinfo("Hint", "You've already used your hint!")


    def update_display(self):
        self.word_label.config(text=" ".join(self.guessed_word))
        self.update_status()
        self.update_points()

    def update_status(self):
        self.status_label.config(text=f"Wrong guesses: {self.wrong_guesses}/{self.max_wrong_guesses}")

    def update_points(self):
        self.points_label.config(text=f"Points: {self.points}")

    def end_game(self, win):
        if win:
            self.total_points += self.points  # Add current level points to total points
            messagebox.showinfo("Congratulations!", f"You guessed the word '{self.word_to_guess}'! Your score: {self.points} | Total Score: {self.total_points}")
            self.level += 1  # Increment the level
            self.update_level()  # Update the level display
            self.update_difficulty()  # Adjust difficulty for the next level
            self.reset_game()  # Reset the game for the next round
        else:
            messagebox.showinfo("Game Over", f"You lost! The word was '{self.word_to_guess}'.")
            self.back_to_home()  # Return to home page after a loss

    def update_level(self):
        """Update the level label to reflect the current level."""
        self.level_label.config(text=f"Level: {self.level}")

    def update_difficulty(self):
        """Adjusts the difficulty for the next level."""
        if self.level == 2:
            self.word_length_range = (4, 6)  # Example adjustment for level 2
        elif self.level == 3:
            self.word_length_range = (7, 9)  # Example adjustment for level 3
        elif self.level > 3:
            self.word_length_range = (10, 12)  # Harder words for higher levels


    def reset_game(self):
        self.word_to_guess, self.clue = self.get_random_word()
        if not self.word_to_guess:
            return  # Exit if no valid words were found
        self.guessed_word = ["_"] * len(self.word_to_guess)
        self.guessed_letters = []
        self.wrong_guesses = 0
        self.points = self.total_points  # Carry over cumulative points
        self.hint_used = False
        self.hint_index = 0
        self.update_display()


    def back_to_home(self):
        self.root.destroy()  # Close the game window
        self.main_root.deiconify()  # Show the main menu


class MainMenu:
    def __init__(self, root):
        self.root = root
        self.root.title("Main Menu")
        self.root.geometry("600x400")
        self.root.configure(bg="#f0f8ff")

        self.db = Database()  # Initialize database connection

        title = tk.Label(self.root, text="Word Guessing Game", font=("Arial", 24, "bold"), bg="#f0f8ff", fg="#4682b4")
        title.pack(pady=10)

        self.signup_button = self.create_button("Sign Up", self.show_signup)
        self.signup_button.pack(pady=10)

        self.login_button = self.create_button("Login", self.show_login)
        self.login_button.pack(pady=10)

        self.exit_button = self.create_button("Exit", self.root.quit, "#ff4500")
        self.exit_button.pack(pady=10)

    def create_button(self, text, command, bg_color="#4682b4"):
        button = tk.Button(self.root, text=text, command=command, bg=bg_color, fg="#ffffff", font=("Arial", 14))
        button.bind("<Enter>", lambda e: button.config(bg="#5bc0de"))
        button.bind("<Leave>", lambda e: button.config(bg=bg_color))
        button.config(pady=10, padx=20)
        return button

    def show_signup(self):
        self.signup_window = tk.Toplevel(self.root)
        self.signup_window.title("Sign Up")
        self.signup_window.geometry("400x300")
        self.signup_window.configure(bg="#f0f8ff")

        tk.Label(self.signup_window, text="Username:", bg="#f0f8ff").pack(pady=5)
        self.username_entry = tk.Entry(self.signup_window)
        self.username_entry.pack(pady=5)

        tk.Label(self.signup_window, text="Password:", bg="#f0f8ff").pack(pady=5)
        self.password_entry = tk.Entry(self.signup_window, show="*")
        self.password_entry.pack(pady=5)

        tk.Button(self.signup_window, text="Sign Up", command=self.signup_user).pack(pady=10)

    def signup_user(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if self.db.add_user(username, password):
            messagebox.showinfo("Success", "User registered successfully!")
            self.signup_window.destroy()  # Close sign-up window
        else:
            messagebox.showerror("Error", "Username already exists!")

    def show_login(self):
        self.login_window = tk.Toplevel(self.root)
        self.login_window.title("Login")
        self.login_window.geometry("400x300")
        self.login_window.configure(bg="#f0f8ff")

        tk.Label(self.login_window, text="Username:", bg="#f0f8ff").pack(pady=5)
        self.login_username_entry = tk.Entry(self.login_window)
        self.login_username_entry.pack(pady=5)

        tk.Label(self.login_window, text="Password:", bg="#f0f8ff").pack(pady=5)
        self.login_password_entry = tk.Entry(self.login_window, show="*")
        self.login_password_entry.pack(pady=5)

        tk.Button(self.login_window, text="Login", command=self.login_user).pack(pady=10)

    def login_user(self):
        username = self.login_username_entry.get()
        password = self.login_password_entry.get()

        if self.db.validate_user(username, password):
            self.login_window.destroy()  # Close login window
            self.show_difficulty_selection()
        else:
            messagebox.showerror("Error", "Invalid username or password.")

    def show_difficulty_selection(self):
        self.difficulty_window = tk.Toplevel(self.root)
        self.difficulty_window.title("Select Difficulty")
        self.difficulty_window.geometry("400x300")
        self.difficulty_window.configure(bg="#f0f8ff")

        tk.Label(self.difficulty_window, text="Select Difficulty Level", font=("Arial", 16), bg="#f0f8ff").pack(pady=10)

        easy_button = tk.Button(self.difficulty_window, text="Easy", command=lambda: self.start_game("Easy"), bg="#4682b4", fg="#ffffff")
        easy_button.pack(pady=5)

        medium_button = tk.Button(self.difficulty_window, text="Medium", command=lambda: self.start_game("Medium"), bg="#4682b4", fg="#ffffff")
        medium_button.pack(pady=5)

        hard_button = tk.Button(self.difficulty_window, text="Hard", command=lambda: self.start_game("Hard"), bg="#4682b4", fg="#ffffff")
        hard_button.pack(pady=5)

    def start_game(self, difficulty):
        self.difficulty_window.destroy()  # Close difficulty selection
        self.root.withdraw()  # Hide main menu
        game_window = tk.Toplevel(self.root)
        WordGuessingGame(game_window, self.root, difficulty, self.db)  # Start the game


if __name__ == "__main__":
    root = tk.Tk()
    main_menu = MainMenu(root)
    root.mainloop()
