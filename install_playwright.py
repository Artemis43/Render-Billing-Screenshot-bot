import subprocess

def install_playwright_dependencies1():
    subprocess.run(["playwright", "install"], check=True)

def install_playwright_dependencies2():
    subprocess.run(["playwright", "install-deps"], check=True)

if __name__ == '__main__':
    install_playwright_dependencies1(), install_playwright_dependencies2()
