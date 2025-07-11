# Portfolio-Project-5

# Zouzou's Fitness 

## Introduction

Zouzou’s Fitness is a Django‑powered web platform for fitness enthusiasts to browse and purchase wellness products like supplements, vitamins, training machines, activewear, shoes, bands, blocks, yoga mats ans so on. The useres can manage their shopping bag, book classes, and securely check out via Stripe. It also includes user registration/login, profile management, and an admin interface for CRUD operations on products and classes. This project is the Code Institute’s Django portfolio project. The Fitness system logic was inspired by the precedent project on code's institute course. This website was created as a learning exercise for my Code Institute portfolio project 5. The live app can be found [here](https://project-portfolio5-82d29c509b78.herokuapp.com/).

## Features

### User Features

- **Browse & View Classes**
  - View a list of available fitness classes (Yoga, Pilates, HIIT, etc.)
  - Filter by instructor, date, price, or time
  - View class details including time, instructor, price and spots left

- **Book a Class**
  - Book a class with a one-time payment
  - Add/cancel bookings from the user dashboard

- **Account & Profile**
  - User registration and login/logout
  - View upcoming and past bookings
  - Manage profile info (email, name, etc.)

### Admin Features

- **Class Management**
  - Add/edit/delete classes, schedule, price and instructors via the Django admin
  - Set capacity limits per class
  - View class bookings and occupancy

## Technologies Used

- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Backend**: Python, Django
- **Database**: PostgreSQL
- **Payments**: Stripe API + Webhooks
- **Deployment**: Heroku / Render (TBD), AWS S3 for static/media files

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Hawraa7/Portfolio-Project-5
   cd zouzous-fitness
   ```

2. **Create a virtual environment and install dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

3. **Django Packages**
Django installs a few packages by default and some packages get installed with other packages. Will list out the ones that I installed.

- crispy bootstrap : django-crispy-bootstrap5 provides you with a crispy-forms template pack to use with django-crispy-forms in your Django projects.
- Django: Django is a high-level Python Web framework that encourages rapid development and clean, pragmatic design.
- Django-allauth: integrated set of Django applications addressing authentication, registration, account management as well as 3rd party (social) account authentication.
- Django-storages : Django Storages is a collection of custom storage backends for Django.
- Pillow: PIL is the Python Imaging Library.
- Psycopg2: Psycopg is the most popular PostgreSQL database adapter for the Python programming language. Its main features are the complete implementation of the Python DB API 2.0 specification and thread safety (several threads can share the same connection). It was designed for heavily multi-threaded applications that create and destroy lots of cursors and make a large number of concurrent “INSERT”s or “UPDATE”s.
- whitenoise:  With a couple of lines of config WhiteNoise allows your web app to serve its own static files, making it a self-contained unit that can be deployed anywhere. 

4. **Set up environment variables:**

   Create a `.env` file and add the following:

   ```env
   SECRET_KEY= os.environ.setdefault('SECRET_KEY')
   DEBUG=True
   STRIPE_PUBLIC_KEY= os.environ.setdefault('STRIPE_PUBLIC_SECRET')
   STRIPE_SECRET_KEY= os.environ.setdefault('STRIPE_SECRET_KEY')
   STRIPE_WEBHOOK_SECRET= os.environ.setdefault('STRIPE_WH_SECRET')
   ```

5. **Migrate the database and load fixtures:**
   ```bash
   python manage.py migrate
   python manage.py loaddata classes/fixtures/initial_classes.json
   ```

6. **Run the server:**
   ```bash
   python manage.py runserver
   ```

## Stripe Integration

- One-time class payments use Stripe Checkout Sessions
- Buy and Pay mutilple products 

## Deployment Checklist

- Disable DEBUG and set `ALLOWED_HOSTS`
- Use PostgreSQL in production
- Setup AWS S3 for static/media
- Set Stripe keys for live mode
- Add webhook endpoints to Stripe dashboard

## Other tools and programs
- Products images used in the project were sourced from [Pexels](https://www.pexels.com/), [Unsplash](https://unsplash.com) which provide free high-quality images. Some images were also generated using AI tools like [Chatgpt](https://chatgpt.com), [Gemini](https://gemini.google.com/).
- Icons used in the project were taken from [Font Awesome](https://fontawesome.com/).
- [Visual Studio Code](https://code.visualstudio.com/) did all of my coding and synchronizing with GitHub on VS Code.
- [GitHub](https://github.com/) : for hosting repositories.
- [Heroku](https://www.heroku.com/) where the website is deployed.

## Testing
Each feature of the application was manually tested to ensure that it works as intended. The following actions were performed:

Navigation Links: Checked that all navigation links work correctly and direct the user to the appropriate page.<>

Product Display: Confirmed fitness products show properly with images, descriptions, and prices.

Class Booking System: Tested that users can select class dates and times, book spots and pay for a book.

Booking Management: Ensured users can view, and cancel their class bookings without errors.

Payment: Verified that payment options work correctly for both one-time class payments.

Admin Controls: Confirmed admins can manage products, classes, bookings, through the admin panel.

User Authentication: Checked that users can securely register, log in, and log out with appropriate validation.

## Code Validation and performance testing
### Google Lighthouse Validation

All pages were tested with Google Chrome Lighthouse. Testing was performed in private browsing mode and on the live website on Heroku.

### CSS Validation

No errors were found when passing through the official W3C validator.

### HTML Validation

All pages were passed through the official W3C validator. Validating was done by a live website on Heroku. Some errors were found but they are all related to Django templates.

### JavaScript Validation

The static JavaScript file was passed through the official JSHint validator.

### PEP8 Code Institute Python Linter Validation

All Python files were passed through the Code Institute PEP8 validator.

### Cross-Browser Testing

The website was tested on the following browsers:

Google Chrome

Mozilla Firefox

Microsoft Edge

Safari

All features functioned as expected across different browsers.

### Responsive Design Testing

The site was tested on multiple screen sizes to ensure it is fully responsive:

Desktop (1920x1080)

Laptop (1366x768)

Tablet (768x1024)

Mobile (375x667) Results:

Navigation and layout adjusted dynamically.

The reservation system remained accessible and easy to use.

Images and text resized correctly without breaking layouts.

### Validator Testing

- HTML

No errors were returned when passing through the official [W3C validator](https://validator.w3.org/).

- CSS

No errors found via the official W3C [(Jigsaw) validator](https://jigsaw.w3.org/css-validator/).

- Python

Code quality checked with flake8 for [PEP8 compliance](https://pep8ci.herokuapp.com/).


## Unfixed Bugs

No known unfixed bugs were found during testing. All identified issues were addressed to ensure smooth functionality across different devices, browsers, and user scenarios. The system has been thoroughly tested for usability, performance, and responsiveness.

## Deployment

The site was deployed to GitHub pages. The steps to deploy are as follows:

- Ensure dependencies are up to date by running:
  - pip freeze > requirements.txt
- Create a Procfile in the root directory with the following content:
  - web: gunicorn bookingrestaurant.wsgi
- Create a new Heroku app
- Set environment variables in Heroku:
  - set DEBUG=False
- heroku config-var:
  - set DATABASE_URL= my_database_url
  - and others secret_key 
- Run database migrations on Heroku
- Push the project to Heroku
- Manual deploy in heroku 
- Open App or click View when you see: Your app was successfully deployed. Once the deployment process is completed, the application will be live on Heroku and accessible through the provided URL: (https://project-portfolio5-82d29c509b78.herokuapp.com/)

## Content

- All written content in the project was created by Me.
-Some UI/UX ideas were inspired by popular fitness websites, and the booking system logic was inspired by the precedent project on Code's Institute course and blogs.
- Django documentation was used as a reference for implementing models and views.
- The deployment steps were adapted from the official Heroku documentation (Heroku Docs).

## Credits

I would like to say thanks to all for the support throughout the project.

- Code Institute for all the support and knowledge.
- Slack community tech-humour channel where I got the inspiration for this project and some feedback. My cohort channel for all the support and feedback.
- My mentor Diego Pupato who's continuously very supportive of me and very knowledgeable.
- I would also like to thank or say sorry to my family. I'm not too sure they have seen me much these past weeks.