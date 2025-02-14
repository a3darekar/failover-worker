# Failover Worker Script 

## Introduction

Lorem ipsum dolor sit amet, consectetur adipisicing elit. Distinctio aperiam pariatur omnis aliquid perspiciatis porro recusandae voluptatibus, magnam iusto, minus odit deserunt enim ipsa corrupti saepe totam at et ullam.

----

## Implementation

### Install python

For Windows:

1. Download Installer from [here](https://www.python.org/downloads/windows/) and Install python 3 (preferably version 3.7 or higher)

2. Follow [this guide](https://www.howtogeek.com/197947/how-to-install-python-on-windows/) in case of any issues. 

3. Check if installation is successful by running given command in command prompt.
	
	$ python3 –version
	
4. If installed properly, The output should read installed version of python.

5. **Note:** Run the command prompt as administer for executing this program.

For Linux:

1. Refer to [this guide](https://docs.python-guide.org/starting/install3/linux/) to install and verify python installation.

### Install pip (package installer for python)

pip is the reference Python package manager. It’s used to install and update packages. You’ll need to make sure you have the latest version of pip installed.

Windows Installer for Python include pip by default. 
Debian and most other linux distributions include a [python-pip](https://packages.debian.org/stable/python-pip) package.
To verify the version, use 
	
	$ py -m pip --version
	
You can make sure that pip is up-to-date by running:

	$ py -m pip install --upgrade pip'

### Install virtualenv using pip

[virtualenv](https://packaging.python.org/key_projects/#virtualenv) is used to manage Python packages for different projects. Using virtualenv allows you to avoid installing Python packages globally which could break system tools or other projects. You can install virtualenv using pip.

On Windows:

	$ py -m pip install --user virtualenv

On macOS and Linux:

	$ python3 -m pip install --user virtualenv

### Clone the repository:

Download the repository from github with the help of [this guide](https://help.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository). Once completing the cloning of the repository, enter into the failover_worker directory and Create and activate a virtual Environment.

### Creating Virtual Environment

venv (For python2) and virtualenv (for python2) allow you to manage separate package installations for different projects. They essentially allow you to create a “virtual” isolated Python installation and install packages into that virtual installation.

To create a virtual environment, go to your project’s directory and run venv. If you are using Python 2, replace venv with virtualenv in the below commands.

On macOS and Linux:

	$ python3 -m venv env

or

	$ python -m virtualenv env

On Windows:

	$ py -m venv env

The second argument is the location to create the virtual environment. Generally, you can just create this in your project and call it env.

venv will create a virtual Python installation in the env folder.

### Activating Virtual Environment

Before you can start installing or using packages in your virtual environment you’ll need to activate it. Activating a virtual environment will put the virtual environment-specific python and pip executables into your shell’s PATH.

After entering  

On macOS and Linux:

	$ source env/bin/activate

On Windows:

	$ .\env\Scripts\activate

### Leaving Virtual Environment

To leave virtual environment, simply run:
	$ deactivate

### Installing packages

Once you activate virtual environment, you can proceed to install packages. For example, to install requests library, run:

	$ pip install requests

or for specific version:

	$ pip install requests==2.18.4

As we already have all requirements specified in the requirements.txt file, we will skip this part and install requirements from 'requirements.txt'

### Using requirements files:

To install requrirements from requirements file, run:

	$ pip install -r requirements.txt

### Update Server url and Node ID:

Open the config.py in a text editor and update the *APP_URL* with your server system's url 

	
	APP_URL = "http://127.0.0.1" 

In the same file update the node id *0* to appropriate number according to your configuration.


### Execute Application script:

After successfully installing all requirements, run the application:

On Windows:

	$ py client.py

On MacOS and Linux:

	$ python client.py

	or

	$ python3 client.py

Once confirmed, Stop this execution by hitting Ctrl + C.

###  Deploying the application as a service 

#### For Windows

The simplest way is to use the: NSSM - the Non-Sucking Service Manager:
1. Download the appropriate version of nssm application from (here)[https://nssm.cc/download]
- Copy the *nssm.exe* to accessible location and traverse to the file in windows prompt and run  

	c:>nssm.exe install WinService

- On NSSM´s console, enter follwoing values and apply other appropriate settings accordingly:

	path: <Environment_path_here>\Scripts\python.exe

	Startup directory: <Project_path_here>

	Arguments: <Project_path_here>\client.py

- check the created service on **services.msc**

#### For Linux

follow the step 7 of setting up a service (here)[https://github.com/knowhere1998/failover-master#step-7-create-systemd-service-file]

#### For MacOS

Follow the steps in (this answer)[https://stackoverflow.com/a/5527943]



## Logging functionality:

Logging is a means of tracking events that happen when some software runs. The logging calls are added to the code to indicate that certain events have occurred. An event is described by a descriptive message which can optionally contain variable data (i.e. data that is potentially different for each occurrence of the event). Events also have an importance which the developer ascribes to the event; the importance can also be called the level or severity.

This program generates 2 distinct logs.
1. First for keep alive log generate by periodic ping (ping.log) and
1. second for maintaining logs generated by communication events with the master node.

### Levels of Logs

	1. DEBUG	Detailed information, typically of interest only when diagnosing problems.
	2. INFO		Confirmation that things are working as expected.
	3. WARNING	An indication that something unexpected happened, or indicative of some problem in the near future. The software is still working as expected.
	4. ERROR	Due to a more serious problem, the software has not been able to perform some function.
	5. CRITICAL	A serious error, indicating that the program itself may be unable to continue running.

### Format followed by the logger is:

	'[TIMESTAMP] [LOGGERNAME] [LOG LEVEL] - [Message]'
