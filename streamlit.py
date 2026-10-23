import streamlit as st
import pandas as pd

st.title("My Streamlit App")
st.write("This is a simple Streamlit application.")


l1 = [1, 2, 3, 4, 5]
st.write(l1)

l2 = [10, 20, 30, 40, 50]
st.write(l2)

df = pd.DataFrame({
    "Column 1": l1,
    "Column 2": l2
})
st.write(df)

name = st.text_input("Enter your name:")
if name:
    st.write(f"Hello, {name}!")

x = st.number_input("Enter a number:", min_value=1, max_value=150)
st.write(f"You entered: {x}")

clicked = st.button("Click me!")
if clicked:
    st.write("Button clicked!")

agree = st.checkbox("I agree")
if agree:
    st.write("You agreed!")
food = st.radio("Choose your favorite food:", ("Pizza", "Burger", "Sushi"))
st.write(f"You selected: {food}")

# ...existing code...

llms = ["GPT-4", "Claude", "Gemini", "Mistral", "LLaMA", "Falcon"]
llm = st.selectbox("Choose your preferred LLM:", llms, index=0)
st.write(f"You selected: {llm}")

x = st.slider("Select a value:", min_value=0, max_value=100, value=50)
st.write(f"You selected: {x}")

st.file_uploader("Upload a file:", type=["csv", "txt"])

# camera_photo = st.camera_input("Take a photo:")
# if camera_photo:
#     st.image(camera_photo)




