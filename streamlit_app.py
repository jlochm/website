import streamlit as st
import sqlite3

# Connect to the database
conn = sqlite3.connect('user_data.db')
cursor = conn.cursor()

# Create the user database if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT,
        last_name TEXT,
        username TEXT UNIQUE,
        password TEXT
    )
''')

# Create the product database if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_name TEXT,
        product_category TEXT,
        product_amount INT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
''')

# Page 1: Registration and Login
def page1():
    st.title("# Supply Chain Services by JLL")

    st.sidebar.header("Navigation")
    page = st.sidebar.radio("Navigation", ["Login", "Registrierung"])

    if page == "Login":
        st.sidebar.header("Login")
        username = st.text_input("Benutzername")
        password = st.text_input("Passwort", type="password")

        if st.button("Anmelden"):
            cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
            user = cursor.fetchone()

            if user:
                st.session_state.user = user 
                st.session_state.page = "page2"  
            else:
                st.error("Ungültige Anmeldeinformationen. Bitte versuchen Sie es erneut.")

    elif page == "Registrierung":
        st.sidebar.header("Registrierung")
        first_name = st.text_input("Vorname")
        last_name = st.text_input("Nachname")
        new_username = st.text_input("Neuer Benutzername")
        new_password = st.text_input("Neues Passwort", type="password")

        if st.button("Registrierung abschließen"):
            try:
                cursor.execute(
                    "INSERT INTO users (first_name, last_name, username, password) VALUES (?, ?, ?, ?)",
                    (first_name, last_name, new_username, new_password)
                )
                conn.commit()
                st.success("Registrierung erfolgreich! Sie können sich jetzt anmelden.")
            except sqlite3.IntegrityError:
                st.error("Benutzername bereits vergeben. Bitte wählen Sie einen anderen.")

# Page 2: Menu
def page2():
    st.title("Wählen Sie Ihren Service")
    
    st.write(f"Willkommen, {st.session_state.user[1]} {st.session_state.user[2]}")
    
    if st.button("Produkt hinzufügen"):
        st.session_state.page = "page3"  # Redirect to Page 3 for adding a product
    
    if st.button("Produktportfolio analysieren"):
        st.session_state.page = "page4"  # Redirect to Page 4 for product portfolio analysis

# Page 3: Product Addition
# Page 3: Product Addition
def page3():
    st.title("Fügen Sie ein Produkt zu Ihrem Portfolio hinzu")

    # Product addition form
    product_name = st.text_input("Produktname")

    # Retrieve unique product categories from the database
    cursor.execute("SELECT DISTINCT product_category FROM products")
    product_categories = [row[0] for row in cursor.fetchall()]

    # Display a selectbox for product categories with an "Other" option
    selected_category = st.selectbox("Produktkategorie auswählen oder neue Kategorie eingeben", product_categories + ["Andere"])

    # If the user selects "Andere," allow them to type in a new category
    if selected_category == "Andere":
        new_category = st.text_input("Neue Produktkategorie")
    else:
        new_category = selected_category

    product_amount = st.text_input("Produktmenge")

    if st.button("Produkt hinzufügen", key="add_product_button"):  # Unique key
        try:
            # Insert product into the database and associate it with the logged-in user
            cursor.execute(
                "INSERT INTO products (user_id, product_name, product_category, product_amount) VALUES (?, ?, ?, ?)",
                (st.session_state.user[0], product_name, new_category, product_amount)
            )
            conn.commit()
            st.success("Produkt erfolgreich hinzugefügt!")
        except sqlite3.Error as e:
            st.error(f"Fehler beim Hinzufügen des Produkts: {e}")

    # Add a button to navigate back to Page 1 (the login window)
    if st.button("Zurück zum Login", key="back_to_login_button"):  # Unique key
        st.session_state.page = "page1"

    # Adding a button to re-navigate to the second page
    if st.button("Zurück zu Menu Auswahl", key="back_to_menu_button"):
        st.session_state.page = "page2"




# Page 4: Placeholder for Product Portfolio Analysis (You can fill this later)
def page4():
    st.title("Produktportfolio analysieren")
    st.write("This is Page 4. You can add content for product portfolio analysis here.")

# Main app
def main():
    if "user" not in st.session_state:
        st.session_state.user = None

    if "page" not in st.session_state:
        st.session_state.page = "page1"

    if st.session_state.page == "page1":
        page1()
    elif st.session_state.page == "page2":
        page2()
    elif st.session_state.page == "page3":
        page3()
    elif st.session_state.page == "page4":
        page4()

# Run the app
if __name__ == "__main__":
    main()

# Datenbankverbindung schließen
conn.close()
