"""Seed vocabulary: skills (name, category, aliases), relation groups and sample jobs."""

# (name, category, [aliases])
SKILLS = [
    # languages
    ("Python", "language", ["python3"]), ("Java", "language", ["core java", "java 8", "java 11", "java 17"]),
    ("JavaScript", "language", ["js", "ecmascript", "es6"]), ("TypeScript", "language", ["ts"]),
    ("C", "language", ["c programming", "c language"]), ("C++", "language", ["cpp"]),
    ("C#", "language", ["csharp", "c sharp"]), ("Go", "language", ["golang"]),
    ("Kotlin", "language", []), ("PHP", "language", []), ("Ruby", "language", []),
    ("R", "language", ["r programming", "r language"]), ("SQL", "language", ["t-sql", "pl/sql", "plsql"]),
    ("Bash", "language", ["shell scripting", "shell"]),
    # backend
    ("Django", "backend", []), ("Flask", "backend", []), ("FastAPI", "backend", []),
    ("Spring Boot", "backend", ["springboot", "spring"]), ("Hibernate", "backend", ["jpa"]),
    ("Node.js", "backend", ["nodejs", "node js", "node"]), ("Express.js", "backend", ["express", "expressjs"]),
    ("REST API", "backend", ["rest apis", "restful", "restful api", "restful apis", "rest"]),
    ("GraphQL", "backend", []), ("Microservices", "backend", ["micro-services", "microservice"]),
    ("Django REST Framework", "backend", ["drf"]), ("JWT", "backend", ["json web token", "json web tokens"]),
    ("OAuth", "backend", ["oauth2", "oauth 2.0"]), ("Celery", "backend", []),
    ("System Design", "backend", ["low level design", "high level design", "hld", "lld"]),
    # frontend
    ("HTML", "frontend", ["html5"]), ("CSS", "frontend", ["css3"]), ("Bootstrap", "frontend", []),
    ("Tailwind CSS", "frontend", ["tailwind"]), ("React", "frontend", ["react.js", "reactjs", "react js"]),
    ("Redux", "frontend", []), ("Angular", "frontend", ["angularjs"]), ("Vue.js", "frontend", ["vue", "vuejs"]),
    ("Next.js", "frontend", ["nextjs"]), ("jQuery", "frontend", []),
    # databases
    ("MySQL", "database", []), ("PostgreSQL", "database", ["postgres"]), ("MongoDB", "database", ["mongo"]),
    ("SQLite", "database", []), ("Oracle", "database", ["oracle db"]), ("Redis", "database", []),
    ("Firebase", "database", ["firestore"]), ("Elasticsearch", "database", ["elastic search"]),
    ("SQL Server", "database", ["mssql", "ms sql"]),
    # cloud / devops
    ("AWS", "cloud", ["amazon web services", "ec2", "s3 bucket"]), ("Azure", "cloud", ["microsoft azure"]),
    ("GCP", "cloud", ["google cloud", "google cloud platform"]), ("Docker", "cloud", ["containers", "containerization"]),
    ("Kubernetes", "cloud", ["k8s"]), ("CI/CD", "cloud", ["ci cd", "continuous integration", "continuous delivery"]),
    ("Jenkins", "cloud", []), ("GitHub Actions", "cloud", []), ("Linux", "cloud", ["ubuntu", "unix"]),
    ("Nginx", "cloud", []), ("Terraform", "cloud", []),
    # data / ml
    ("Pandas", "data", []), ("NumPy", "data", []), ("scikit-learn", "data", ["sklearn", "scikit learn"]),
    ("TensorFlow", "data", []), ("PyTorch", "data", []), ("Keras", "data", []),
    ("Machine Learning", "data", ["ml"]), ("Deep Learning", "data", ["neural networks"]),
    ("NLP", "data", ["natural language processing"]), ("spaCy", "data", []), ("NLTK", "data", []),
    ("Sentence Transformers", "data", ["sentence-transformers", "sbert", "sentence embeddings"]),
    ("Computer Vision", "data", ["opencv"]), ("Data Analysis", "data", ["data analytics", "exploratory data analysis", "eda"]),
    ("Data Visualization", "data", ["matplotlib", "seaborn", "plotly"]), ("Power BI", "data", ["powerbi"]),
    ("Tableau", "data", []), ("Excel", "data", ["ms excel", "microsoft excel"]), ("Statistics", "data", ["statistical analysis"]),
    ("Spark", "data", ["pyspark", "apache spark"]), ("Hadoop", "data", []), ("ETL", "data", ["data pipelines", "data pipeline"]),
    ("Generative AI", "data", ["genai", "llm", "llms", "large language models"]),
    # tools / practices
    ("Git", "tools", []), ("GitHub", "tools", []), ("GitLab", "tools", []), ("Jira", "tools", []),
    ("Postman", "tools", []), ("Maven", "tools", []), ("Gradle", "tools", []), ("Agile", "tools", ["scrum", "kanban"]),
    ("Unit Testing", "tools", ["junit", "pytest", "unittest", "test driven development", "tdd"]),
    ("Selenium", "tools", []), ("Figma", "tools", []), ("Data Structures", "tools", ["dsa", "data structures and algorithms", "algorithms"]),
    ("OOP", "tools", ["object oriented programming", "object-oriented programming", "object oriented design"]),
    ("Design Patterns", "tools", []), ("Multithreading", "tools", ["concurrency"]),
    # soft
    ("Communication", "soft", ["communication skills"]), ("Teamwork", "soft", ["collaboration", "team player"]),
    ("Leadership", "soft", []), ("Problem Solving", "soft", ["problem-solving", "analytical skills"]),
    ("Time Management", "soft", []),
]

# Groups of skills that partially transfer to each other.
RELATED_GROUPS = [
    ["MySQL", "PostgreSQL", "SQL Server", "Oracle", "SQLite", "SQL"],
    ["MongoDB", "Firebase", "Redis", "Elasticsearch"],
    ["Django", "Flask", "FastAPI", "Django REST Framework"],
    ["Spring Boot", "Hibernate", "Django", "Node.js", "Express.js"],
    ["React", "Angular", "Vue.js", "Next.js", "Redux"],
    ["HTML", "CSS", "Bootstrap", "Tailwind CSS"],
    ["JavaScript", "TypeScript", "Node.js"],
    ["Java", "Kotlin", "C#", "C++"],
    ["AWS", "Azure", "GCP"],
    ["Docker", "Kubernetes", "CI/CD", "Jenkins", "GitHub Actions"],
    ["TensorFlow", "PyTorch", "Keras", "Deep Learning"],
    ["Machine Learning", "scikit-learn", "Deep Learning", "Statistics", "NLP"],
    ["NLP", "spaCy", "NLTK", "Sentence Transformers", "Generative AI"],
    ["Pandas", "NumPy", "Data Analysis", "Excel"],
    ["Power BI", "Tableau", "Data Visualization"],
    ["Git", "GitHub", "GitLab"],
    ["REST API", "GraphQL", "Microservices", "JWT", "OAuth"],
    ["Unit Testing", "Selenium", "Postman"],
    ["Spark", "Hadoop", "ETL"],
    ["OOP", "Design Patterns", "System Design", "Data Structures"],
]

# Sample jobs (title, company, location, type, level, description)
JOBS = [
    ("Java Full Stack Developer", "FinPay Technologies", "Mumbai", "full_time", "entry",
     "Build payment dashboards using Java, Spring Boot, Hibernate and React. Design REST APIs, work with MySQL, "
     "write unit tests with JUnit, use Git and Docker. Understanding of microservices and system design is a plus."),
    ("Backend Engineer (Python)", "LedgerLoop", "Bengaluru", "full_time", "entry",
     "Develop scalable backend services with Python, Django and Django REST Framework. Work with PostgreSQL, Redis and "
     "Celery. Deploy with Docker on AWS. Strong data structures, REST API design and unit testing skills required."),
    ("Data Analyst", "InsightWorks", "Pune", "full_time", "entry",
     "Analyse business data using SQL, Python, Pandas and Excel. Build dashboards in Power BI or Tableau. "
     "Strong statistics, data visualization and communication skills needed."),
    ("Machine Learning Engineer", "NeuralNest", "Hyderabad", "full_time", "mid",
     "Design and deploy machine learning models using Python, scikit-learn, TensorFlow or PyTorch. Experience with NLP, "
     "Pandas, NumPy, Docker and AWS. Familiarity with MLOps, CI/CD and Git is required."),
    ("NLP Engineer", "LinguaAI", "Remote", "remote", "mid",
     "Work on NLP pipelines: text classification, information extraction and semantic search using spaCy, NLTK and "
     "Sentence Transformers. Strong Python, scikit-learn and REST API skills. Knowledge of Generative AI is a plus."),
    ("Frontend Developer (React)", "PixelForge", "Mumbai", "full_time", "entry",
     "Build responsive interfaces with React, JavaScript, TypeScript, HTML and CSS. Use Redux, Bootstrap or Tailwind CSS. "
     "Consume REST APIs and collaborate using Git and Agile."),
    ("Software Development Intern", "CodeCraft Labs", "Mumbai", "internship", "entry",
     "Internship for students strong in data structures, OOP and problem solving. Work with Java or Python, SQL and Git. "
     "Exposure to Spring Boot or Django and REST APIs is welcome."),
    ("DevOps Engineer", "CloudBridge", "Bengaluru", "full_time", "mid",
     "Manage CI/CD pipelines with Jenkins and GitHub Actions. Containerize with Docker and orchestrate with Kubernetes on AWS. "
     "Linux, Terraform and Bash scripting experience required."),
    ("Full Stack Developer (Django + React)", "StackSprint", "Remote", "remote", "entry",
     "End-to-end feature development using Django, React, MySQL, HTML, CSS and JavaScript. Build REST APIs, integrate JWT "
     "authentication, and deploy with Docker. Git and Agile experience preferred."),
    ("Data Scientist", "QuantLeaf", "Bengaluru", "full_time", "mid",
     "Apply statistics and machine learning on large datasets using Python, Pandas, NumPy and scikit-learn. Build "
     "data visualization, run experiments, and communicate insights. SQL and Spark knowledge is a plus."),
]
