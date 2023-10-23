import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
import io
import base64


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
        product_year INT,
        product_month TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
''')

# Page 1: Registration and Login
def page1():
    st.title("Supply Chain Services by JLL")

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
    
    product_year = st.text_input("Jahr")
    
    product_month = st.text_input("Monat")

    if st.button("Produkt hinzufügen", key="add_product_button"):  # Unique key
        try:
            # Insert product into the database and associate it with the logged-in user
            cursor.execute(
                "INSERT INTO products (user_id, product_name, product_category, product_amount, product_year, product_month) VALUES (?, ?, ?, ?, ?, ?)",
                (st.session_state.user[0], product_name, new_category, product_amount, product_year, product_month)
            )
            conn.commit()
            st.success("Produkt erfolgreich hinzugefügt!")
        except sqlite3.Error as e:
            st.error(f"Fehler beim Hinzufügen des Produkts: {e}")

    # Add a button to navigate back to Page 1 (the login window)
    if st.button("Zurück zum Login", key="back_to_login_button"):  # Unique key
        st.session_state.page = "page1"

    # Adding a button to re-navigate to the second page
    if st.button("Zurück zur Menüauswahl", key="back_to_menu_button"):
        st.session_state.page = "page2"

        
        
# Function that enables to download a plot as a png
def download_plot_as_png(plt):
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    return buffer


# Defining the fourth page
def page4():
    st.title("Produktportfolio analysieren")

    # User input: Analyze by product name or category
    analyze_by = st.radio("Analyse nach", ["Produktnamen", "Produktkategorie"])

    if analyze_by == "Produktnamen":
        # Retrieve existing product names from the database
        cursor.execute("SELECT DISTINCT product_name FROM products")
        existing_names = [row[0] for row in cursor.fetchall()]

        # User input: Select a product name
        selected_name = st.selectbox("Produktnamen auswählen", existing_names)

        # Retrieve data for the selected product name
        cursor.execute("SELECT product_year, product_amount FROM products WHERE user_id = ? AND product_name = ?", (st.session_state.user[0], selected_name))
    else:  # Analyze by product category
        # Retrieve existing product categories from the database
        cursor.execute("SELECT DISTINCT product_category FROM products")
        existing_categories = [row[0] for row in cursor.fetchall()]

        # User input: Select a product category
        selected_category = st.selectbox("Produktkategorie auswählen", existing_categories)

        # Retrieve data for the selected product category
        cursor.execute("SELECT product_year, SUM(product_amount) FROM products WHERE user_id = ? AND product_category = ? GROUP BY product_year", (st.session_state.user[0], selected_category))

    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=["Year", "Amount"])

    # Perform the statistical analysis (Random Forest Regression, for example)
    X = df["Year"].values.reshape(-1, 1)
    y = df["Amount"].values
    regressor = RandomForestRegressor(n_estimators=100, random_state=0)
    regressor.fit(X, y)

    # Generate predictions for the next two years
    future_years = [2023, 2024]
    future_predictions = regressor.predict([[year] for year in future_years])

    plt.figure(figsize=(15, 11))
    plt.plot(df["Year"], df["Amount"], label="Actual Data")
    plt.plot(future_years, future_predictions, label="Predicted Data")
    plt.xlabel("Year")
    plt.ylabel("Product Amount")
    plt.legend()
    plt.title("Product Portfolio Analysis")

    # Display the plot in Streamlit
    st.pyplot(plt)

    # Add a download button for the plot image
    download_buffer = download_plot_as_png(plt)
    st.download_button(
        label="Download Plot as png",
        data=download_buffer,
        file_name="product_portfolio_analysis.png",
        key="download_png_button")
    
        # Adding a button to re-navigate to the second page
    if st.button("Zurück zur Menüauswahl", key="back_to_menu_button"):
        st.session_state.page = "page2"
    
    
    
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

