import concurrent.futures as cf
import csv
import os
import requests
import sys
import threading

DIR = os.path.dirname(os.path.realpath(__file__))
SPRINGER_FILE = os.path.join(DIR, 'springer.csv')
SPRINGER_FOLDER = os.path.join(DIR, 'Bookstore')
SPRINGER_DOWLOAD = "https://link.springer.com/content/pdf"
MAX_THREAD = 4

# progress bar
current_state = 0
max_state = 0


def download(filename, url, sherif):
    global current_state

    # filename UNIX style
    isbn = url.split('=')[-1].replace('-', '')
    filename = filename.replace(' ', '_') + '-' + isbn
    file_path = os.path.join(SPRINGER_FOLDER, filename + ".pdf")

    if not os.path.exists(file_path):
        # Create download URL by accessing to redirected URL
        page_url = requests.get(url).url.split('/')[-1]  # Get the last part (book ref)
        download_url = '/'.join([SPRINGER_DOWLOAD, page_url + ".pdf"])

        # Download the PDF
        pdf = requests.get(download_url, stream=True)

        # Create the new file and put the content in
        new_book = open(file_path, "wb")
        new_book.write(pdf.content)
        new_book.close()

        # Locking the thread because...
        # yeah we like concurrent programming
        with sherif:
            # this shows progress
            current_state += 1
            sys.stdout.write('\r')
            sys.stdout.write('PDF {}/{}, downloaded: {}'.format(current_state, max_state, filename))
            sys.stdout.flush()
    else:
        with sherif:
            # this shows progress
            current_state += 1
            sys.stdout.write('\r')
            sys.stdout.write('PDF {}/{}, present: {}'.format(current_state, max_state, filename))
            sys.stdout.flush()


def main():
    global max_state

    # My brother made me do this, I think this is just plain boring,
    # and I like to managed thread like if I'm a Sherif in the wild wild west
    sherif = threading.Lock()

    # Create directory
    if not os.path.exists(SPRINGER_FOLDER):
        os.mkdir(SPRINGER_FOLDER)

    with open(SPRINGER_FILE) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=';')
        next(csv_reader, None)

        with cf.ThreadPoolExecutor(max_workers=MAX_THREAD) as executor:
            pipe = [executor.submit(download, book[0], book[1], sherif) for book in csv_reader]
            max_state = len(pipe)
            cf.wait(pipe)


if __name__ == "__main__":
    # execute only if run as a script
    main()
