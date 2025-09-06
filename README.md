# South African Intervarsity Hackathon Submission Template - 2025

Welcome to the official **Hackathon Submission Template** for the **South African Intervarsity Hackathon 2025**! This repository is designed to help participants organize their project submissions in a **consistent, judge-friendly structure** while supporting any tech stack.

---

## 📂 Repository Structure
```
├── assets/
│   └── README.md
├── demo/
│   └── README.md
├── docs/
│   ├── ACKNOWLEDGEMENTS.md
│   ├── OVERVIEW.md
│   ├── SETUP.md
│   ├── TEAM.md
│   └── USAGE.md
├── scripts/
│   └── README.md
├── src/
│   └── README.md
├── vendor/
│   └── README.md
├── .dockerignore
├── .editorconfig
├── .gitattributes
├── .gitignore
├── DockerFile
├── LICENSE
└── README.md
```
---

### 🔹 Description of Each Folder/File

- **assets/**  
    All assets used by your project such as **images**, **audio files**, **3D models**, **datasets** and so-on, should be placed in this folder.

- **demo/**  
    Your **demo video**, **PowerPoint presentation** and or any **examples** should be placed in this folder.

- **docs/**  
    Contains essential documentation about your team and project (these must be written by you):
    - `ACKNOWLEDGEMENTS.md` → References all third-party libraries and sources used
    - `OVERVIEW.md` → Project overview and key features  
    - `SETUP.md` → Instructions for installing dependencies and running the project  
    - `TEAM.md` → Team member names, roles, and contact info  
    - `USAGE.md` → Instructions for using or testing the project 

- **scripts/**  
    All **utility**, **automation** and **project-management** scripts should be placed in this folder.

- **src/**  
    All source code files should be placed in this folder. You may organize this folder as needed (e.g., `backend/`, `frontend/`, `lib/`, `source/` and or `include/` folders and so on).

- **vendor/**  
    All third-party libraries, code and or submodules should be placed in this folder along **with the appropriate licensing and or references**. If you are not able to link the modules from this folder to your codebase properly, you may put the third-party modules inside the `src/` folder with the rest of your code however, it **must be made clear** which modules are **third-party**, along with their **licensing**.
    Since many tech-stacks already use package managers, this `vendor/` folder is for self-included libraries, dependencies and submodules. **Auto-generated** dependency folders like `node_modules/` or `nuget/` should ideally be ignored by `.gitignore`.

- **.dockerignore**  
    Excludes build artifacts and other non-essential files from the Docker image. *You may delete this file if you do not plan on using Docker.*

- **.editorconfig**  
    Standardizes indentation, line endings, and character encoding across editors and platforms. It is **highly recommended** that you use a text editor/IDE that supports **.editorconfig**.

- **.gitattributes**  
    Ensures consistent handling of line endings, text, and binary files across different operating systems.

- **.gitignore**  
    Ignores build artifacts, OS files, IDE configs, and other non-essential files to keep the repository clean.

- **Dockerfile**  
    A "quick start" template **Dockerfile** to serve as a blueprint for containerizing your project in a **Docker image**. *You may delete this file if you do not plan on using Docker.*

- **LICENSE**  
    Default license template for your submission (MIT recommended).
    *You must add the names of your team members to this template.*

- **README.md**  
    Hey wait, that's me!

---

## ✅ Submission Guidelines

1. Create your project's repo off of this template (click the `Use this template` button).  
2. Fill in the `TEAM.md` file with your team members’ information. 
3. Start hacking!
4. Fill in `ACKNOWLEDGEMENTS.md`, `OVERVIEW.md`, `SETUP.md`, `USAGE.md` and `LICENSE`. 
5. Link or include your demo video & PowerPoint in the `demo/` folder.  
6. **Optional:** Include additional documentation and design notes in `docs/`.
7. **Optional:** Include unit tests in `tests/`.
8. Submit the link to your **public GitHub repository**.

---

## 📌 Tips

- Keep your code and assets organized within `src/` and `assets/`.  
- Use `.editorconfig` and `.gitattributes` to avoid formatting and line-ending issues.  
- Follow the folder structure strictly — it will make judging smoother and faster.  

---

Good luck and happy hacking! 🚀

## Brought to you by??? Maybe idk
