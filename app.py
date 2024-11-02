from groq import Groq
import streamlit as st
import os
import json
import zipfile
from tempfile import NamedTemporaryFile
import time


#--------------------------------------------------------------------------------------------------------------------------------------------------

def extract_zip(zip_file, extract_dir):
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

def create_directory_tree(root_dir):
    tree = {}
    for root, dirs, files in os.walk(root_dir):
        current_dir = tree
        for dir_name in root.split(os.sep)[1:]:
            current_dir = current_dir.setdefault(dir_name, {})
        for file_name in files:
            file_path = os.path.join(root, file_name)
            # Check if file extension is in a list of non-code file types
            if not is_code_file(file_name):
                continue
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
            except UnicodeDecodeError:
                with open(file_path, 'rb') as file:
                    content = file.read().decode('latin-1')
            current_dir[file_name] = content
    return tree

def is_code_file(file_name):
    non_code_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', '.ppt', '.pptx']
    # Check if the file has an extension that indicates it's not a code file
    return not any(file_name.lower().endswith(ext) for ext in non_code_extensions)


def preprocess_code(code):
    preprocessed_code = []
    for snippet in code:
        # Remove comments
        snippet = remove_comments(snippet)
        # Remove unnecessary whitespace
        snippet = snippet.strip()
        # Tokenize code
        tokens = tokenize_code(snippet)
        preprocessed_code.append(tokens)
    return preprocessed_code

def remove_comments(code):
    lines = code.split('\n')
    code_without_comments = []
    for line in lines:
        # Remove single-line comments
        if '//' in line:
            line = line[:line.index('//')]
        code_without_comments.append(line)
    return '\n'.join(code_without_comments)

def tokenize_code(code):
    # Simple tokenization by splitting on whitespace
    return code.split()

def analyze_code(code_contents):
    contents = ""
    for filename, code in code_contents.items():
        contents +=f"\nCode from file '{filename}':"
        contents += f"\n\n{code}\n\n"
        contents += '-' * 20
    return contents

def load_json(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data

def extract_code_contents(json_data):
    code_contents = {}
    for directory, files in json_data.items():
        for filename, content in files.items():
            code_contents[filename] = content
    return code_contents

def extracting(zip_file_path):
    zip_file = zip_file_path  # Replace 'your_zip_file.zip' with the path to your zip file
    extract_dir = 'extracted_files'  # Directory to extract the contents of the zip file
    output_json = 'directory_tree.json'  # Output JSON file to store the directory tree and file contents

    try:
        # Extract zip file
        extract_zip(zip_file, extract_dir)
        
        # Create directory tree
        directory_tree = create_directory_tree(extract_dir)

        # Save directory tree to JSON
        with open(output_json, 'w') as json_file:
            json.dump(directory_tree, json_file, indent=4)

        # Load JSON data
        
        json_data = load_json(output_json)
        
        # Extract code contents
        code_contents = extract_code_contents(json_data)
        
        # Analyze code
        contents_of_code = analyze_code(code_contents)

        # Return code contents
        return contents_of_code, json_data
    except Exception as e:
        print(f"An error occurred: {e}")
        # If an error occurs, return None
        return None



#--------------------------------------------------------------------------------------------------------------------------------------------------


def getResponseAsJSON(prompt):
    client = Groq(api_key='YOUR_API_KEY')  # Replace 'YOUR_API_KEY' with your Groq API key

    response = client.chat.completions.create(
        messages=[
            {
                "role":"system",
                "content":f"json {prompt}",
                
            }
        ],
        model="llama3-8b-8192",
        response_format={"type": "json_object"},
        # max_tokens=32000,

    )

    return response

def getResponse(prompt):
    client = Groq(api_key='YOUR_API_KEY')  # Replace 'YOUR_API_KEY' with your Groq API key

    response = client.chat.completions.create(
        messages=[
            {
                "role":"system",
                "content":f"{prompt}",
                
            }
        ],
        model="llama3-8b-8192",
        # max_tokens=32000,

    )

    return response



def getContent(response):
    return response.choices[0].message.content



def checkWarning(response):
     # Extract the text from the response
    text = response.choices[0].message.content.strip().lower()
    
    # Split the response into words
    words = text.split()
    
    # Check if the first word is "yes" or "no"
    if words[0] == "Yes":
        st.write("Yes")
        return 1
    if words[0] == "No":
        st.write("No")
        return 0
    else:
        return None  # If the first word is neither "yes" nor "no"




def analyze_codebase_with_llama(json_data, code_contents, desired_code):



    while True:
        prompt_cc = None
        prompt_convert = None
        # Construct prompt for code analysis
        prompt_warning = construct_warning(json_data, code_contents, desired_code)
        
        response_warning= getResponse(prompt_warning)

        if checkWarning(response_warning):
            #analyze_groq_response(response_warning, 'Warning')
            st.warning("Please select another code language.")
            exit()

        prompt_cc = construct_prompt_cc(json_data, code_contents, desired_code)

        prompt_test_case = construct_prompt_test_case(json_data, code_contents)

        prompt_documentation = construct_prompt_documentation(json_data, code_contents)
        response_doc = getResponse(prompt_documentation)

        response_cc = getResponse(prompt_cc)

        response_test_case = getResponse(prompt_test_case)

        prompt_convert = construct_prompt_convert(json_data, code_contents, getContent(response_cc))

        response_convert = getResponse(prompt_convert)

        prompt_forTest = construct_prompt_forTest(response_test_case, getContent(response_convert))

        # prompt_code_check = construct_prompt_code_check(getContent(response_convert), code_contents)

        #response_checkCode = getResponseAsJSON(prompt_code_check)

        response_testResult = getResponseAsJSON(prompt_forTest)
        
        data1 = json.loads(response_testResult.choices[0].message.content)
        # data2 = json.loads(response_checkCode.choices[0].message.content)
        acc = data1["accuracy"]
        acc_str = "Accuracy: "+str(acc) + "/10"
        # convertCheck = data2[0]
        # print(convertCheck)
        # if not(int(convertCheck)):
        #     continue
        if int(acc) >= 9:
            break

        time.sleep(4)




    

    # Process and interpret Groq response
    
    analyze_groq_response(response_doc, 'Technical Documentation')
    #analyze_groq_response_JSON(response_testResult, 'Test result')
    st.subheader(f"{acc_str}")
    analyze_groq_response(response_convert, 'Codes Converted')

    #extract_json_from_response(getContent(response_convert))


def construct_warning(json_data, code_contents, desired_code):

    prompt = f"Can the Code contents be converted to {desired_code}.\n"
    prompt += f"Code Contents: {code_contents}. \n "
    prompt += f"The First word of the response should be 'Yes' if the Code Contents can't be converted to {desired_code}, 'No' if it can be converted.\n"
    prompt += "Send an warning if it can't be converted as a response."
    prompt += "Compose a comprehensive technical documentation detailing the architecture, functionality, and usage of the codebase. Include sections covering the system overview, design patterns employed, key modules/components, API references, data structures, algorithms, dependencies, installation instructions, configuration options, and usage examples. Additionally, provide insights into best practices, troubleshooting tips, and potential future enhancements. Your documentation should cater to both developers new to the project and seasoned contributors seeking deeper insights.\n"

    return prompt

def construct_prompt_documentation(json_data, code_contents):

    prompt = "Generate technical documentation based on the provided code snippet.\n"
    prompt += f"Code Contents: {code_contents}.\n"
    prompt += "Return Technical Documentation on all codes.\n"
    prompt += "DO IT FOR ALL CODES.\n"
    prompt += """ What is Technical Documentation?
Technical documentation encompasses any written material that elucidates the application, purpose, creation, or architecture of a product or service. Its primary objective is to elucidate aspects of what an organization offers. This documentation can take various forms, including how-to guides, user manuals, presentations, memos, reports, and more.

Who Creates Technical Documentation?
Technical documentation is typically crafted by technical writers, project managers, development team members, or subject matter experts. Various industries rely on technical documentation, including software, automotive, healthcare, and consumer products sectors.

Audience for Technical Documents
The audience for technical documents varies based on the document type. End users often interact with product-related documentation, while internal stakeholders and clients may engage with documentation pertaining to development processes, project progress, or technical specifications.

Importance of Technical Documentation
Technical documentation plays a pivotal role in facilitating understanding and usage of a product or service. For end users, it enables efficient product utilization and troubleshooting, potentially reducing the need for customer support. Internally, it enhances productivity and aligns teams by providing clear guidance and reference materials.

Types of Technical Documentation
Two primary categories of technical documentation are process documentation and user documentation. Process documentation delineates the development lifecycle of a product, while user documentation focuses on providing guidance to end users on product usage, troubleshooting, and features.

How to Create Technical Documentation
Have a Plan: Develop an outline detailing the components to include in the documentation.
Understand Your Audience: Tailor the documentation style and content to suit the intended audience's knowledge level and preferences.
Create a First Draft: Use templates or outlines to structure the document and include all necessary information.
Consider Adding Images: Visual aids such as diagrams and charts enhance understanding, especially for complex topics.
Review the Document: Solicit feedback from team members and subject matter experts to refine and update the document as needed.
Tips for Writing Technical Documentation
Be Consistent: Maintain uniformity in appearance, style, and tone throughout the document to enhance readability.
Be Concise: Edit the document to eliminate unnecessary or ambiguous content, focusing on conveying key information succinctly.
Optimize for Multiple Platforms: Ensure accessibility across various devices and platforms to maximize usability for the audience.
By adhering to these guidelines, you can create technical documentation that effectively communicates critical information and meets the needs of your audience.
                """

    return prompt

def construct_prompt_test_case(json_data, code_contents):

    prompt = f"Write test cases for all codes in the: \n {code_contents}\n"
    prompt += "Atleast 10 cases for each code in all aspects"

    return prompt

def construct_prompt_code_check(response, code_contents):

    prompt = f"CHECK WHETHER ALL CODE IN CODE CONTENTS:\n {code_contents}\n\n"
    prompt += f"Is converted in the below contents:\n {response}.\n\n"
    prompt += "THE RESPONSE IS IN JSON FORMAT . Keyword be 'check' AND ITS VALUE BE 0 if it is not converted correctly or 1 if it is converted correctly.\n"


def construct_prompt_cc(json_data, code_contents, desired_code):
    prompt = "Analyse the provided code contents and determine the appropriate programming language for each file.\n"
    prompt += f"Understand the complete codebase and identify any dependencies or relationships between the code snippets.\n"
    prompt += "- The codebase is extracted from a directory structure stored in a JSON file.\n"
    prompt += "- It contains multiple code snippets representing various functionalities.\n\n"
    prompt += "Your task is to:\n"
    prompt += "1. Identify the main funtionality of all programming languages used in the codebase.\n"
    prompt += f"2. Determine which files need to be converted to {desired_code}.\n"
    prompt += f"3. If conversion to {desired_code} is not feasible, suggest modern age coding languages as alternatives.\n\n"
    prompt += "But all the codes must and should be instucted to be converted, and all the fountionality of the codes must be analysed and instructed correctly.\n"
    prompt += "In your response, include:\n"
    prompt += "- A list of files and the recommended programming language for each.\n"
    prompt += "- Detailed instructions on how to convert each file to the recommended language.\n"
    prompt += "- Algorithms, methodologies, or tools required for the conversion.\n\n"
    prompt += "Code Contents:\n"
    prompt += code_contents
    return prompt



def construct_prompt_convert(json_data, code_contents, convert_instructions):
    prompt = "Analyse the following conversion instructions carefully:\n\n"
    prompt += f"{convert_instructions}\n\n"
    prompt += "All the codes must and should be converted"
    prompt += "Using the provided instructions, convert all code snippets accordingly.\n"
    prompt += "- Code Contents:\n"
    prompt += f"{code_contents}\n"
    prompt += "\n- Enclose the converted code with triple backticks (```) at the start and end.\n"
    prompt += "- Example:\n"
    prompt += "  ```code```\n"
    prompt += "DO NOT ASK ANY QUESTIONS AND CONVERT THE CODES. Do not skip codes, all the codes must and should be converted, Only give the converted code not the previous code.\n"
    prompt += "DO NOT ADD - Your code goes here, and so on, implement the code here, BUT YOU SHOULD COMPLETELY CONVERT ALL CODES WITHOUT LEAVEING ANYTHIB OUT.\n "
    # prompt += "\n- Ensure that  triple backticks are not repeated elsewhere except for enclosing the JSON code.\n"
    # prompt += r"  ```{ JSON FILE }```"
    
    return prompt

def construct_prompt_forTest(response_test_case, response_convert):

    prompt = "It is in JSON FORMAT. Test all the test cases for each code and calculate the accuracy of the tests passed marked out of 10 based on the Converted code by automatically by yourself.\n"
    prompt += f"Converted code: {response_convert}\n"
    prompt += f"Test case: {response_test_case}\n"
    prompt += "Only one word response of the marks out of 10. and its keyword be 'accuracy'"
    prompt += r"{'accuracy':marks} <- in this format"
    return prompt

def analyze_groq_response_JSON(response, subHead):
    # Process and interpret Groq response
    st.subheader(f"{subHead}:")
    st.write(response.choices[0].message)

def analyze_groq_response(response, subHead):
    # Process and interpret Groq response
    st.subheader(f"{subHead}:")
    st.write(response.choices[0].message.content)




# Function to save uploaded file to temporary location
def save_uploaded_file(uploaded_file):
    with NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.read())
        return tmp_file.name


def main():
    st.title("CodeRevive")
    contents_of_code = None
    json_data = None

    # File upload section
    st.subheader("Upload Zip File")
    zip_file = st.file_uploader("Upload your zip file", type="zip")
    if zip_file:
        # Save uploaded file to temporary location
        zip_file_path = save_uploaded_file(zip_file)
        st.success("Zip file uploaded successfully!")

        st.sidebar.header("Settings")
        languages = ["Python", "Java", "C++", "JavaScript", "Go"]  # List of available languages
        # Allow user to input a custom language
        custom_language = st.sidebar.text_input("Custom Language")

        # Multiselect widget for selecting languages
        selected_languages = st.sidebar.multiselect("Desired Code Languages", languages)

        # Use the selected languages if they are present, otherwise use the custom language
        desired_code = selected_languages if selected_languages else [custom_language] if custom_language else []

        if st.sidebar.button("Analyze Codebase"):
            if zip_file is not None:
                
                contents_of_code, json_data = extracting(zip_file_path)
                # print(contents_of_code)
                # print(json_data)
                analyze_codebase_with_llama(json_data, contents_of_code, desired_code)
            else:   
                st.warning("Please upload a zip file.")

    else:
        st.warning("Please upload a zip file.")

if __name__ == "__main__":
    main()
