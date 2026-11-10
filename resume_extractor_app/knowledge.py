"""Curated knowledge base used to validate and correct the model's keyword predictions.

Edit these lists freely: add a term to TECH or SKILLS and it will always be recognised
(and put in the right category), even if the model misses it.
"""

TECH = """
Python|Java|JavaScript|TypeScript|C|C++|C#|Go|Golang|Rust|Kotlin|Swift|Objective-C|PHP|Ruby|Scala|R|Perl|Dart|Julia|MATLAB|
Bash|Shell Scripting|PowerShell|SQL|PL/SQL|T-SQL|NoSQL|HTML|HTML5|CSS|CSS3|Sass|SCSS|Less|XML|JSON|YAML|GraphQL|Solidity|Assembly|
VHDL|Verilog|Haskell|Elixir|Lua|Groovy|COBOL|Fortran|Visual Basic|VBA|
React|React.js|ReactJS|React Native|Angular|AngularJS|Vue|Vue.js|Svelte|Next.js|Nuxt.js|Gatsby|jQuery|Redux|Bootstrap|Tailwind CSS|
Tailwind|Material UI|Chakra UI|Three.js|D3.js|Chart.js|Node.js|NodeJS|Express|Express.js|NestJS|Deno|Bun|Django|Django REST Framework|
Flask|FastAPI|Spring|Spring Boot|Hibernate|Struts|Laravel|Symfony|CodeIgniter|Ruby on Rails|Rails|ASP.NET|.NET|.NET Core|Blazor|
Flutter|Xamarin|Ionic|SwiftUI|Jetpack Compose|Android|Android Studio|iOS|Xcode|Electron|Qt|Streamlit|Gradio|
TensorFlow|Keras|PyTorch|Scikit-learn|sklearn|Pandas|NumPy|SciPy|Matplotlib|Seaborn|Plotly|OpenCV|NLTK|spaCy|Gensim|Hugging Face|
Transformers|LangChain|LlamaIndex|XGBoost|LightGBM|CatBoost|YOLO|MediaPipe|Jupyter|Jupyter Notebook|Google Colab|Anaconda|
OpenAI API|ChatGPT|Gemini|Claude|Ollama|MLflow|Kubeflow|Weights & Biases|ONNX|TensorRT|CUDA|
MySQL|PostgreSQL|Postgres|SQLite|MongoDB|Redis|Oracle|Oracle Database|SQL Server|Microsoft SQL Server|MariaDB|Cassandra|DynamoDB|
Firebase|Firestore|Supabase|Elasticsearch|Neo4j|CouchDB|Snowflake|BigQuery|Redshift|Databricks|Hive|HBase|
Apache Spark|Spark|PySpark|Hadoop|Kafka|Apache Kafka|Airflow|Apache Airflow|Flink|dbt|Talend|Informatica|SSIS|
AWS|Amazon Web Services|EC2|S3|Lambda|Azure|Microsoft Azure|GCP|Google Cloud|Google Cloud Platform|Heroku|Netlify|Vercel|
DigitalOcean|Cloudflare|Docker|Kubernetes|K8s|Terraform|Ansible|Puppet|Chef|Jenkins|GitHub Actions|GitLab CI|CircleCI|Travis CI|
Nginx|Apache|Tomcat|Linux|Ubuntu|Kali Linux|Windows|macOS|Unix|Red Hat|CentOS|
Git|GitHub|GitLab|Bitbucket|SVN|Jira|Confluence|Trello|Asana|Notion|Slack|Postman|Swagger|Insomnia|
Figma|Adobe XD|Sketch|Canva|Photoshop|Adobe Photoshop|Illustrator|Adobe Illustrator|Premiere Pro|After Effects|Blender|
AutoCAD|SolidWorks|CATIA|ANSYS|Revit|SketchUp|Unity|Unreal Engine|Godot|
Excel|Microsoft Excel|MS Excel|Power BI|Tableau|Looker|Qlik|Google Sheets|Google Analytics|SAP|Salesforce|ServiceNow|
MS Office|Microsoft Office|Word|PowerPoint|Outlook|Visual Studio|VS Code|Visual Studio Code|IntelliJ|IntelliJ IDEA|PyCharm|
Eclipse|NetBeans|Vim|Selenium|Cypress|Playwright|Jest|Mocha|JUnit|PyTest|TestNG|Cucumber|Appium|JMeter|LoadRunner|
Arduino|Raspberry Pi|ESP32|ESP8266|NodeMCU|Proteus|Multisim|LabVIEW|Simulink|Keil|PLC|SCADA|ThingSpeak|MQTT|
Wireshark|Nmap|Metasploit|Burp Suite|Splunk|Snort|John the Ripper|Hydra|Nessus|OWASP ZAP|
REST API|REST APIs|RESTful APIs|gRPC|WebSockets|OAuth|JWT|Socket.IO|RabbitMQ|Celery|Prometheus|Grafana|ELK Stack|Kibana|Logstash|
WordPress|Shopify|Magento|Drupal|Webflow|Wix|Zapier|UiPath|Blue Prism|Power Automate|Power Apps|Maven|Gradle|npm|Yarn|Webpack|Vite|
Babel|Linux Shell|Hyperledger|Ethereum|Web3.js|Truffle|Hardhat
"""

SKILLS = """
Machine Learning|Deep Learning|Artificial Intelligence|AI|ML|Generative AI|GenAI|Natural Language Processing|NLP|Computer Vision|
Data Science|Data Analysis|Data Analytics|Data Visualization|Data Engineering|Data Mining|Data Modeling|Data Cleaning|
Data Preprocessing|Data Wrangling|Big Data|Business Intelligence|Business Analysis|Statistical Analysis|Statistical Modeling|
Statistics|Predictive Modeling|Predictive Analytics|Feature Engineering|Time Series Forecasting|A/B Testing|Reinforcement Learning|
Neural Networks|Prompt Engineering|Large Language Models|LLMs|MLOps|Model Deployment|ETL|Data Warehousing|
Web Development|Frontend Development|Front-end Development|Backend Development|Back-end Development|Full Stack Development|
Mobile App Development|App Development|Android Development|iOS Development|Game Development|Software Development|
Software Engineering|API Development|Microservices|System Design|Object Oriented Programming|OOP|OOPS|Data Structures|Algorithms|
Data Structures and Algorithms|DSA|Database Design|Database Management|DBMS|Operating Systems|Computer Networks|Networking|
Cloud Computing|DevOps|CI/CD|Version Control|Unit Testing|Software Testing|Manual Testing|Automation Testing|Test Automation|
Quality Assurance|Debugging|Code Review|Performance Optimization|Agile|Scrum|Kanban|SDLC|Responsive Web Design|Responsive Design|
UI Design|UX Design|UI/UX|UI/UX Design|UX Research|Wireframing|Prototyping|Graphic Design|Web Design|
Cybersecurity|Cyber Security|Network Security|Information Security|Ethical Hacking|Penetration Testing|Vulnerability Assessment|
Digital Forensics|Cryptography|Incident Response|Threat Analysis|Risk Assessment|
Internet of Things|IoT|Embedded Systems|Robotics|Automation|Blockchain|AR/VR|Augmented Reality|Virtual Reality|
Digital Marketing|SEO|Content Writing|Technical Writing|Social Media Marketing|Copywriting|
Project Management|Product Management|Stakeholder Management|Requirement Analysis|Requirements Gathering|
Problem Solving|Problem-Solving|Critical Thinking|Analytical Thinking|Analytical Skills|Communication|Communication Skills|
Teamwork|Team Work|Collaboration|Leadership|Team Leadership|Team Management|Time Management|Adaptability|Creativity|
Attention to Detail|Decision Making|Presentation Skills|Public Speaking|Negotiation|Mentoring|Customer Service|
Conflict Resolution|Self-Motivated|Interpersonal Skills|Multitasking|Event Management|Research
"""

# Common words that are never keywords on their own.
GENERIC = set("""
a an the and or of in on at to for from with by as is are was were be been being it its this that these those i me my we our you your
he she they them their his her new old good great best strong solid excellent basic advanced intermediate beginner proficient familiar
knowledge experience experienced hands-on hands on gaining gained gain learn learned learning built build building developed develop
developing created create creating designed design designing worked work working used use using implemented implement made make
including include various multiple several many more most other others also well very highly key core main major minor
technology technologies technical tech tools tool skills skill software hardware system systems solution solutions application
applications app apps project projects platform platforms service services product products process processes data team teams
company companies client clients user users customer customers business industry field domain area areas role roles level levels
student students intern internship internships trainee fresher engineer engineers developer developers analyst analysts manager
management member members head lead associate assistant senior junior graduate undergraduate bachelor master degree diploma
college university institute school academy department course courses certification certifications certificate training workshop
seminar conference competition competitions quiz event events club activities activity achievements achievement award awards
summary profile objective education career contact email phone address location date place present current ongoing
year years month months day days time january february march april may june july august september october november december
jan feb mar apr jun jul aug sep sept oct nov dec part full remote onsite hybrid india indian kerala
responsible responsibilities task tasks duty duties result results feature features page pages website websites web online offline
interest interests hobby hobbies reading travelling music sports cricket football
""".split())

COMPANY_WORDS = {"llp", "ltd", "pvt", "inc", "corp", "corporation", "limited", "private", "llc", "gmbh", "co", "solutions",
                 "technologies", "softtech", "infotech", "systems", "labs", "consultancy", "services", "group", "enterprises",
                 "college", "university", "institute", "school", "academy", "foundation", "hospital", "bank"}

PLACES = set("""
kerala tamil nadu karnataka maharashtra telangana andhra pradesh delhi gujarat rajasthan punjab haryana goa odisha bihar
bengal west uttar madhya assam jharkhand chhattisgarh uttarakhand himachal kashmir india usa uk canada australia germany dubai uae
kochi cochin ernakulam trivandrum thiruvananthapuram kozhikode calicut thrissur kottayam kollam kannur palakkad alappuzha malappuram
idukki pathanamthitta wayanad kasaragod bangalore bengaluru chennai hyderabad mumbai pune kolkata noida gurgaon gurugram ahmedabad
coimbatore mysore mangalore madurai london singapore
""".split())

# Short / everyday-English tech names: only accepted from the dictionary scan when capitalised as a name.
AMBIGUOUS = {"go", "c", "r", "swift", "rust", "spring", "express", "excel", "react", "unity", "ruby", "julia", "dart",
             "word", "less", "chef", "puppet", "apache", "windows", "android", "sketch", "notion", "slack", "claude",
             "gemini", "qt", "bun", "research", "automation", "networking", "statistics", "ai", "ml", "seo", "oop", "plc"}

# Variants that should be shown under one canonical name.
ALIASES = {"reactjs": "React", "react.js": "React", "nodejs": "Node.js", "postgres": "PostgreSQL", "sklearn": "Scikit-learn",
           "golang": "Go", "k8s": "Kubernetes", "ms excel": "Excel", "microsoft excel": "Excel", "vs code": "VS Code",
           "visual studio code": "VS Code", "amazon web services": "AWS", "rest apis": "REST API", "restful apis": "REST API",
           "cyber security": "Cybersecurity", "problem-solving": "Problem Solving", "team work": "Teamwork",
           "front-end development": "Frontend Development", "back-end development": "Backend Development",
           "oops": "OOP", "html5": "HTML", "css3": "CSS", "apache spark": "Spark", "apache kafka": "Kafka",
           "apache airflow": "Airflow", "microsoft azure": "Azure", "google cloud platform": "Google Cloud", "gcp": "Google Cloud",
           "adobe photoshop": "Photoshop", "adobe illustrator": "Illustrator", "vue": "Vue.js", "angularjs": "Angular",
           "express": "Express.js", "rails": "Ruby on Rails", "ml": "Machine Learning", "nlp": "Natural Language Processing",
           "iot": "Internet of Things", "ui/ux design": "UI/UX", "communication skills": "Communication",
           "intellij idea": "IntelliJ", "microsoft office": "MS Office", "jupyter notebook": "Jupyter",
           "postgresql": "PostgreSQL", "mongodb": "MongoDB", "mysql": "MySQL", "github": "GitHub"}


def _parse(block):
    return [t.strip() for t in block.replace("\n", "").split("|") if t.strip()]


TECH_LIST = _parse(TECH)
SKILL_LIST = _parse(SKILLS)
