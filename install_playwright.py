import subprocess

def install_playwright_dependencies():
    subprocess.run(["playwright", "install"], check=True)

if __name__ == '__main__':
    install_playwright_dependencies()
