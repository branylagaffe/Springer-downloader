import concurrent.futures as cf
import csv
import os
import requests
import sys
import threading

# File constant
DIR = os.path.dirname(os.path.realpath(__file__))
SPRINGER_FILE = os.path.join(DIR, 'springer.csv')
SPRINGER_FOLDER = os.path.join(DIR, 'Bookstore')
SPRINGER_DOWLOAD = "https://link.springer.com/content/pdf"
MAX_THREAD = 4

# Progress bar
current_state = 0
max_state = 0
stale = 0


def download(filename, url, sherif):
    global current_state
    global stale

    # Filename UNIX style
    isbn = url.split('=')[-1].replace('-', '')
    filename = filename.replace(' ', '_') + '-' + isbn
    file_path = os.path.join(SPRINGER_FOLDER, filename + ".pdf")

    if not os.path.exists(file_path):
        # Parse download URL by accessing to redirected URL
        page_url = requests.get(url).url.split('/')[-1]  # Get the last part (book ref)
        download_url = '/'.join([SPRINGER_DOWLOAD, page_url + ".pdf"])

        # Open PDF link
        pdf = requests.get(download_url, stream=True)

		# If it's not a PDF, it's seen as STALE
        if pdf.headers['content-type'] in ['application/pdf']:
            # Create the new file and put the contents in it
            new_book = open(file_path, "wb")
            new_book.write(pdf.content)
            new_book.close()

            # Locking the thread because...
            # YEAH, we like concurrent programming
            with sherif:
                # Update PDF counter
                current_state += 1
                sys.stdout.write('\r')
                sys.stdout.write(f'{"PDF {}/{}, downloaded: {}": <64}'.format(current_state, max_state, filename))
                sys.stdout.flush()
        else:
        	# Update PDF and STALE counter
            stale += 1
            current_state += 1

    else:
        with sherif:
            # Update PDF counter
            current_state += 1
            sys.stdout.write('\r')
            sys.stdout.write(f'{"PDF {}/{}, present: {}": <64}'.format(current_state, max_state, filename))
            sys.stdout.flush()


def main():
    global max_state

    # My brother made me do this, I think this is just plain boring,
    # and I like to manage thread like the Sherif I would be in the Wild Wild West
    sherif = threading.Lock()

    # Create directory
    if not os.path.exists(SPRINGER_FOLDER):
        os.mkdir(SPRINGER_FOLDER)

	# Open .csv
    with open(SPRINGER_FILE) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        # Skip header
        next(csv_reader, None)

		# Will take care of having constenly 4 thread running to download the PDFs
        with cf.ThreadPoolExecutor(max_workers=MAX_THREAD) as executor:
            pipe = [executor.submit(download, book[0], book[1], sherif) for book in csv_reader]
            max_state = len(pipe) - 1
            cf.wait(pipe)

	# End script and print stats
    print('\nDownloaded {}, found {} stale link'.format(max_state - stale, stale))


if __name__ == "__main__":
    # execute only if run as a script
    main()
