from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
import os
import zipfile
import uuid
import shutil
import re
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import random
from matplotlib.font_manager import FontProperties
import matplotlib.pyplot as plt
import numpy as np

application = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'zip'}
application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Check if the uploaded file is a zip
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@application.route('/')
def list_sims():
    #sim_ids = os.listdir(application.config['UPLOAD_FOLDER'])
    
    with open('sim.json', 'r') as f:
        sims = json.load(f)
    #for sim in sims:
    #    sim["sim_tag"] = sim["sim_type"].capitalize()
    return render_template('index.html', sims=sims)

#@application.route('/')
#def index():
#    sims = os.listdir(application.config['UPLOAD_FOLDER'])
#    return render_template('index.html', sims=sims)
# use env flask i.e. conda activate flask

@application.route('/add_sim', methods=['POST'])
def add_sim():
    if 'file' not in request.files:
        return redirect(request.url)
        # Validation
    sim_name=request.form.get('simName')
    sim_desc=request.form.get('simDesc')
    sim_subject=request.form.get('subject')
    sim_level=request.form.get('level')
    sim_type=request.form.get('type')
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        sim_id = str(uuid.uuid4())
        sim_path = os.path.join(application.config['UPLOAD_FOLDER'], sim_id)
        os.makedirs(sim_path)
        file.save(os.path.join(sim_path, file.filename))
        print(sim_name)
        # Extract the files and rename them
        with zipfile.ZipFile(os.path.join(sim_path, file.filename), 'r') as zip_ref:
            for file_info in zip_ref.infolist():
                extracted_file_path = zip_ref.extract(file_info, path=sim_path)
                
                # Check if the filename is within the specified list
                #allowed_ext = ['.html', '.css', '.js']
                #print(extracted_file_path)
                #root, ext = os.path.splitext(extracted_file_path)
                if("._" in extracted_file_path):
                #if ext not in allowed_ext:
                    continue
                print('passed')
                #print("file_info.filename "  + file_info.filename + ", extracted_file_path: " + extracted_file_path)
                # Modify the HTML content to use the new paths for CSS and JS
                if file_info.filename.endswith('.html'):
                    html_file_path=extracted_file_path
                    with open(extracted_file_path, 'r') as html_file:
                        html_content = html_file.read()
                        # Replace the CSS and JS paths
                        html_content = re.sub(r'href="(?:(?!http|https).)*\.css"', f'href="/sims/{sim_id}/styles.css"', html_content)
                        html_content = re.sub(r'src="(?:(?!http|https).)*\.js"', f'src="/sims/{sim_id}/script.js"', html_content)
                    # Write the modified content back to the file
                elif file_info.filename.endswith('.css'):
                    css_file_path=extracted_file_path
                    with open(extracted_file_path, 'r') as css_file:
                        css_content = css_file.read()
                elif file_info.filename.endswith('.js'):
                    js_file_path=extracted_file_path
                    with open(extracted_file_path, 'r') as js_file:
                        js_content = js_file.read()
        print("Read content")           
        
        html_content,css_content, js_content = modify_class_and_tags(html_content,css_content,js_content, sim_id)           
        
        print("Processed content")           
        
        with open(html_file_path, 'w') as html_file:
            html_file.write(html_content)
        with open(css_file_path, 'w') as css_file:
            css_file.write(css_content)
        with open(js_file_path, 'w') as js_file:
            js_file.write(js_content)
        os.rename(html_file_path, os.path.join(sim_path, "index.html"))
        os.rename(css_file_path, os.path.join(sim_path, "styles.css"))
        os.rename(js_file_path, os.path.join(sim_path, "script.js"))
        os.remove(os.path.join(sim_path, file.filename))

        #print("calling insert_sim")
        
        image_path=generate_image(sim_name,sim_id)
        image=sim_id+".jpg"

        if not os.path.exists('sim.json'):
            with open('sim.json', 'w') as f:
                json.dump([], f)

        with open('sim.json', 'r') as f:
            sims = json.load(f)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sims.applicationend({
            'id': sim_id,
            'image':image,
            'sim_name': sim_name,
            'sim_desc': sim_desc,
            'sim_subject': sim_subject,
            'sim_level': sim_level,
            'sim_type': sim_type,
            'timestamp': timestamp
        })
        print(sims)

        with open('sim.json', 'w') as f:
            json.dump(sims, f)
        #data={'sim_id': sim_id, 'sim_name': sim_name}
        #response = requests.post('http://127.0.0.1:5000/insert_sim', data={'sim_id': sim_id, 'sim_name': sim_name})
        #if response.status_code != 200:
        #    return "Failed to insert simulation metadata", 500
    return redirect(url_for('list_sims'))

# The modified upload function ensures that the extracted files are named as per the standard 
# and the references in the HTML are updated to the new paths.
#upload_sim_final

@application.route('/delete_sim/<sim_id>', methods=['POST','GET'])
def delete_sim(sim_id):
    
    with open('sim.json', 'r') as f:
        sims = json.load(f)

    sims = [sim for sim in sims if sim['id'] != sim_id]

    with open('sim.json', 'w') as f:
        json.dump(sims, f)
                
    sim_path = os.path.join(application.config['UPLOAD_FOLDER'], sim_id)
    
    # Check if the sim directory exists
    if os.path.exists(sim_path):
        # Remove the directory and its contents
        shutil.rmtree(sim_path)
    return redirect(url_for('list_sims'))

@application.route('/update_sim/<sim_id>', methods=['GET', 'POST'])
def update_sim(sim_id):
    if request.method == 'GET':
        # Handle the uploaded file and update the simulation
        # (Using the logic from the `update_sim` function)
        return redirect(url_for('list_sims'))
    else:
        # Render a simple form to upload the new content
        return """
        <form action="/upload/{}" method="post" enctype="multipart/form-data">
            <input type="file" name="file">
            <input type="submit" value="Update">
        </form>
        """.format(sim_id)


#@application.route('/sims/<sim_id>')
#def view_sim(sim_id):
#    return send_from_directory(os.path.join(application.config['UPLOAD_FOLDER'], sim_id), 'index.html')
@application.route('/get_sim/<sim_id>')
def get_sim(sim_id):
    with open('sim.json', 'r') as f:
        sims = json.load(f)
        sim = next((item for item in sims if item["id"] == sim_id), None)
    return jsonify(sim)
    
@application.route('/sims/<sim_id>')
def sim_preview(sim_id):
    # Retrieve simulation details based on sim_id (this might need adjustments based on your setup)
    with open('sim.json', 'r') as f:
        sims = json.load(f)
        sim = next((item for item in sims if item["id"] == sim_id), None)
    
    sim_index_path = os.path.join('uploads', sim_id, 'index.html')
    with open(sim_index_path, 'r') as f:
        index_content = f.read()
    
    # Construct the simulation object with the content of index.html
    sim["index_content"] =  index_content
    return render_template('sim_preview.html', sim=sim)

@application.route('/sims/<sim_id>/styles.css')
def sim_css(sim_id):
    return send_from_directory(os.path.join(application.config['UPLOAD_FOLDER'], sim_id), 'styles.css', mimetype='text/css')

@application.route('/sims/<sim_id>/script.js')
def sim_js(sim_id):
    return send_from_directory(os.path.join(application.config['UPLOAD_FOLDER'], sim_id), 'script.js', mimetype='applicationlication/javascript')

#def create_application():
#    application = Flask(__name__)
#    # other initializations and configurations...
#    return application

def modify_class_and_tags(html_content, css_content, js_content, sim_id):
    """Modify class selectors and tags in the given HTML content based on references in the CSS content."""
    
    soup = BeautifulSoup(html_content, 'html.parser')
    head = soup.find('head')
    script_tags_in_head = head.find_all('script')
    
    body = soup.find('body')
    for script_tag in script_tags_in_head:
        body.applicationend(script_tag)
    #for link in soup.find_all("link", rel="stylesheet"):
    #    link.decompose()  # Remove the link tag

  
    # Regular expression to identify tag selectors and class selectors in the CSS
    tag_selector_pattern = re.compile(r'\b(?!(html|body|head)\b)(\w+)\b')
    class_selector_pattern = re.compile(r'(\.[\w\-]+)')
    
    html_tags = [tag.name for tag in soup.find_all(True)]
    
    pattern = re.compile(r'(?<!\d)([^\{\}]+)(?<!\d)\s*\{', re.MULTILINE)
    
    css_selectors = pattern.findall(css_content)
    
    all_tags = [selector.strip() for selector in css_selectors]
    
    css_tags = []
    for selector in all_tags:
        # Split the selector using spaces and '::' as delimiters to handle compound selectors
        tags = re.split(r'\s+|::', selector)
        # For each tag, remove content after ':' or '::'
        tags = [tag.split(':')[0] for tag in tags]
        css_tags.extend(tag for tag in tags if tag and not tag.endswith('%'))  # Exclude percentage values
    css_tags=set(css_tags)
    
    #pattern = re.compile(r'(?<=[,}\s])(?<![.\#])([a-z][a-z0-9\-]*)\s*\{')
    #pattern = re.compile(r'([^\{\}]+)\s*\{', re.MULTILINE)
    #css_selectors = pattern.findall(css_content)
    #all_tags = [selector.strip() for selector in css_selectors]
    #css_tags = []
    #for selector in all_tags:
    #    print(selector)
    #    split_selectors = [s.strip() for s in selector.split(",")]
    #    css_tags.extend(split_selectors)
   
    # remove "." from selectors in CSS
    css_selectors = [selector[1:] if selector.startswith(".") else selector for selector in css_tags]


   # Shared tags are type selectors that need to be converted to class selectors
    shared_tags = [tag for tag in html_tags if tag in css_tags]
        
    for tag in shared_tags:
        for elem in soup.find_all(tag):
            new_class = f"{tag}-{sim_id}"
            elem['class'] = [new_class]
    
    #css_classes = {match.group(1)[1:] for match in class_selector_pattern.finditer(css_content)}  # Excluding the dot

    # Convert only those tags into class selectors which are referenced in the CSS
    tags=soup.find_all(True)
    for tag in soup.find_all(True):
        current_classes = tag.get('class', [])
        #print(current_classes)
        new_classes = [f"{cls}-{sim_id}" if cls in css_selectors else cls for cls in current_classes]
        if(new_classes):
            print(new_classes)
            tag['class'] = new_classes
    
    # Now convert shared tags in CSS such that it has a sim_id
    for tag in css_tags:
        if(tag in shared_tags):
            class_selector = f".{tag}-{sim_id}"
        else:
            class_selector = f"{tag}-{sim_id}"
        print(class_selector)
        #css_content = css_content.replace(tag, class_selector, 1)
        css_content = re.sub(tag, class_selector,css_content)
        orig_string='querySelector("'+tag+'")'
        repl_string='querySelector("'+class_selector+'")'
        js_content=js_content.replace(orig_string,repl_string)
        orig_string='querySelectorAll("'+tag+'")'
        repl_string='querySelectorAll("'+class_selector+'")'
        js_content=js_content.replace(orig_string,repl_string)

        
    #class_selector_pattern = re.compile(r'(\.[\w\-]+)')
    #new_css_content = class_selector_pattern.sub(lambda match: match.group(1) + f".{sim_id}", css_content)
        
    body_content = soup.body.contents
    
    # Convert the content to a string
    inner_html = ''.join(map(str, body_content))
    inner_html=inner_html.strip()
    return inner_html, css_content, js_content


def generate_gradient(image, color1, color2, angle):
    """Generate a gradient background with a given angle."""
    for i in range(image.shape[1]):
        for j in range(image.shape[0]):
            alpha = (i * np.cos(angle) + j * np.sin(angle)) / (image.shape[1] * np.cos(angle) + image.shape[0] * np.sin(angle))
            image[j, i] = (1 - alpha) * np.array(color1) + alpha * np.array(color2)
    return image


# Convert hex colors to RGB
def hex_to_rgb(value):
    value = value.lstrip('#')
    length = len(value)
    return tuple(int(value[i:i + length // 3], 16) for i in range(0, length, length // 3))

def calculate_luminance(color):
    """Calculate the luminance of a color."""
    r, g, b = color
    return 0.299 * r + 0.587 * g + 0.114 * b

def get_contrasting_color(color):
    """Get a contrasting color (black or white) based on the luminance of the input color."""
    luminance = calculate_luminance(color)
    return (0, 0, 0) if luminance > 127.5 else (255, 255, 255)  # Return black or white

def get_inverted_color(color):
    """Invert the given RGB color."""
    r, g, b = color
    inverted = (255 - int(r), 255 - int(g), 255 - int(b))
    return tuple([val/255 for val in inverted])


def generate_image(phrase,sim_id):
    # Randomly select gradient colors
    
    gradients= [('#2E3192', '#1BFFFF'),('#D4145A', '#FBB03B'),('#009245', '#FCEE21'),('#662D8C', '#ED1E79'),
                ('#EE9CA7', '#FFDDE1'),('#614385', '#516395'),('#02AABD', '#00CDAC'),('#FF512F', '#DD2476'),
                ('#FF5F6D', '#FFC371'),('#11998E', '#38EF7D'),('#C6EA8D', '#FE90AF'),('#EA8D8D', '#A890FE'),
                ('#D8B5FF', '#1EAE98'),('#FF61D2', '#FE9090'),('#BFF098', '#6FD6FF'),('#4E65FF', '#92EFFD'),
                ('#A9F1DF', '#FFBBBB'),('#C33764', '#1D2671'),('#93A5CF', '#E4EfE9'),('#868F96', '#596164'),
                ('#09203F', '#537895'),('#FFECD2', '#FCB69F'),('#A1C4FD', '#C2E9FB'),('#764BA2', '#667EEA'),
                ('#FDFCFB', '#E2D1C3')]

    stopwords = ["i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself", "yourselves",
             "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself", "they", "them", "their",
             "theirs", "themselves", "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are", "was",
             "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an", "the", "and",
             "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", "with", "about", "against", "between",
             "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off",
             "over", "under", "again", "further", "then", "once"]

    available_fonts = ["Arial", "Times New Roman", "Courier New", "Verdana", "Trebuchet MS", "Georgia", "Palatino", "Comic Sans MS"]

    selected_font = random.choice(available_fonts)
    
    keywords = [word for word in phrase.split() if word.lower() not in stopwords and word.lower() != "simulation"]
    selected_keyword = random.choice(keywords)
    
    color1, color2 = random.choice(gradients)
    color1_rgb = hex_to_rgb(color1)
    color2_rgb = hex_to_rgb(color2)

    # Randomly select an angle for the gradient
    angle = random.uniform(0, np.pi)

    # Generate the gradient background with exact dimensions
    image = np.zeros((100, 200, 3))
    generate_gradient(image, color1_rgb, color2_rgb, angle)
    average_color = np.mean(image, axis=(0, 1))
    text_color = get_inverted_color(average_color)
    
    # Create the figure and axis objects with exact size
    fig, ax = plt.subplots(figsize=(2, 1))
    ax.imshow(image/255.0)
    

    font_size=round(36/(len(selected_keyword)/4))
    # Overlay the text at the center
    ax.text(100, 50, selected_keyword.capitalize(), fontname=selected_font, fontsize=font_size, ha='center', va='center', color=text_color)

    # Hide the axis
    ax.axis('off')
    
    # Save the image with fixed size
    image_path = f"static/images/{sim_id}.jpg"
    plt.savefig(image_path, dpi=133, bbox_inches='tight', pad_inches=0, format='jpg')
    
    # Close the plot to free up resources
    plt.close(fig)
    
    return image_path

# Test the function with sample inputs

if __name__ == "__main__":
    application.run(debug=True)


