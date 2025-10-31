# My Django Portfolio

![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![GitHub API](https://img.shields.io/badge/GitHub_API-181717?style=for-the-badge&logo=github&logoColor=white)

Welcome to my **Django Portfolio**! This is a simple yet elegant portfolio website built with **Django** and styled with **Tailwind CSS**. It showcases my skills, about me, and my GitHub projects using the **GitHub API**.

---

## 🌟 Features

- **Three Pages**:
  - **Welcome Page**: A landing page to greet visitors.
  - **About Me**: A page to share information about myself.
  - **Projects**: A page that fetches and displays my GitHub projects using the GitHub API.
- **Modern Design**: Styled with **Tailwind CSS** for a clean and responsive UI.
- **GitHub Integration**: Fetches and displays my GitHub repositories dynamically.

---

## 🛠️ Technologies Used

- **Backend**: Django (Python)
- **Frontend**: HTML, Tailwind CSS
- **APIs**: GitHub API
- **Version Control**: Git & GitHub

---

## 🚀 Installation

To run this project locally, follow these steps:

1. **Clone the repository**:
  ```bash
   git clone https://github.com/django-frog/django-portfolio
   cd django-portfolio
  ```
2. **Set up a virtual environment**:
  ```bash  
  python -m venv venv
  source venv/bin/activate  # On Windows: venv\Scripts\activate
  ```
3. **Install dependencies**:
  ```bash
    pip install -r requirements.txt
  ```

4. **Set up environment variables**:

  Create a .env file in the root directory and add your GitHub API token (optional for public repos):

  ```bash
  cp .test.env .env
  ```

  Then change environment variables:
  ```env
  APP_SECRET = "Django_Application_Secret"
  GITHUB_API = "Github API Url"
  GITHUB_TOKEN = "Your Github account token"

  MEMCACHED_SERVERS = "Memcached Server Address"
  MEMCACHED_PASSWORD = "Memcached Server Poassword"
  MEMCAHCED_USERNAME = "Memcached username"

  MYSQL_DB_NAME = "MySQL database name"
  MYSQL_DB_USER = "MySQL database user"
  MYSQL_DB_HOST = "MySQL database host"
  MYSQL_DB_PASS = "MySQL database password"


  LEETCODE_GRAPHQL_API = "https://leetcode.com/graphql"
  LEETCODE_REST_API = "https://alfa-leetcode-api.onrender.com/"
  LEETCODE_USERNAME = "mohammadAsCP"
  ```
5. **Export Mode System Variable**:
   - *For Production*:
   ```bash
   export DJANGO_SETTINGS_MODULE=portfolio.settings.prod
   ```

   - *For Development*:
   ```bash
   export DJANGO_SETTINGS_MODULE=portfolio.settings.dev
   ``` 

6. **Run migrations**:
  ```bash
  python manage.py migrate
  ```

7. **Collect static files**:
  ```bash
  python manage.py collectstatic
  ```

8. **Compile Language File**
```bash
python manage.py compilemessages
```

9. **Run the development server**:
  ```bash
  python manage.py runserver
  ```

Visit http://127.0.0.1:8000 in your browser to see the project in action!
