import requests
import xml.dom.minidom
import tkinter as tk
import re
import webbrowser

ui_mode = True

def convert_isbn10_to_isbn13(isbn):
    if len(isbn) == 10:
        isbn13_prefix = "978"
        isbn13_without_check = isbn13_prefix + isbn[:9]
        factors = [1, 3] * 6
        sum_ = sum(int(digit) * factor for digit, factor in zip(isbn13_without_check, factors))
        check_digit = (10 - (sum_ % 10)) % 10
        isbn = isbn13_without_check + str(check_digit)
    return isbn


def get_info(isbn):
    title, author, publisher, publication_year, nsfa = None, None, None, None, None

    # Query OCLC API for book information
    url = f"http://classify.oclc.org/classify2/Classify?isbn={isbn}&summary=true"
    response = requests.get(url)

    if response.status_code == 200:
        dom = xml.dom.minidom.parseString(response.text)
        works = dom.getElementsByTagName("work")
        if works:
            work = works[0]
            author = work.getAttribute("author")
            title = work.getAttribute("title")
        recommendations = dom.getElementsByTagName("recommendations")
        if recommendations:
            ddc = recommendations[0].getElementsByTagName("ddc")
            if ddc:
                most_popular = ddc[0].getElementsByTagName("mostPopular")
                if most_popular:
                    nsfa = most_popular[0].getAttribute("nsfa")

    # Query Google Books API for book information
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if data["totalItems"] > 0:
            book_info = data["items"][0]["volumeInfo"]
            title = book_info.get("title")
            authors = book_info.get("authors")
            author = ", ".join(authors) if authors else None
            publisher = book_info.get("publisher")
            publication_year = book_info.get("publishedDate")
            publication_year = publication_year[:4]

    return title, author, publisher, publication_year, nsfa


def get_price(isbn):
    url = "https://www.abebooks.com/servlet/DWRestService/pricingservice"
    payload = {'action': 'getPricingDataByISBN',
               'isbn': isbn,
               'container': 'pricingService-{}'.format(isbn)}
    resp = requests.post(url, data=payload)
    results = resp.json()
    if results['success']:
        book_new, book_used, destination = None, None, None
        best_new = results['pricingInfoForBestNew']
        best_used = results['pricingInfoForBestUsed']
        if best_new != None:
            new_price = best_new['bestPriceInPurchaseCurrencyValueOnly']
            new_shipping = best_new['bestShippingToDestinationPriceInPurchaseCurrencyValueOnly']
            destination = best_new['shippingDestinationNameInSurferLanguage']
        if best_used != None:
            used_price = best_used['bestPriceInPurchaseCurrencyValueOnly']
            used_shipping = best_used['bestShippingToDestinationPriceInPurchaseCurrencyValueOnly']
            destination = best_used['shippingDestinationNameInSurferLanguage']
        
        book_new = (float(new_price)*100+float(new_shipping)*100)/100
        book_used = (float(used_price)*100+float(used_shipping)*100)/100
        return (book_new, book_used, destination)
    return [None, None, None]


def search():
    entry.get().strip().replace('-', '').replace(' ', '')
    isbn = re.sub(r'\D', '', entry.get())

    if len(isbn) not in [10, 13]:
        result.configure(text="Error: ISBN must be 10 or 13 digits")
        return

    if len(isbn) == 10:
        isbn = convert_isbn10_to_isbn13(isbn)

    # Bind the "Return" key to the "search" function
    entry.bind('<Return>', search)

    title, author, publisher, publication_year, ddc = get_info(isbn)
    best_new, best_used, destination = get_price(isbn)

    # Initialize count variable
    count_hidden = 0

    # Build result string, hiding empty fields
    result_text = ""
    if title:
        result_text += f"Title: {title}\n"
    else:
        count_hidden += 1
    if author:
        result_text += f"Author(s): {author}\n"
    else:
        count_hidden += 1
    result_text += f"ISBN: {isbn}\n"
    if ddc:
        result_text += f"DDC: {ddc}\n"
    else:
        count_hidden += 1
    if publisher:
        result_text += f"Publisher: {publisher}\n"
    else:
        count_hidden += 1
    if publication_year:
        result_text += f"Publication Year: {publication_year}\n"
    else:
        count_hidden += 1
    if best_new:
        result_text += f"New Book Price: US$ {best_new} \n"
    else:
        count_hidden += 1
    if best_used:
        result_text += f"Used Book Price: US$ {best_used}\n"
    else:
        count_hidden += 1    
    if destination:
        result_text += f"Shipping To: {destination}\n"
    else:
        count_hidden += 1

        # Show message if any data is hidden
    if count_hidden == 1:
        result_text += f"({count_hidden} empty data entry is hidden)"
    if count_hidden > 1:
        result_text += f"({count_hidden} empty data entries are hidden)"

    link1.config(state='normal')
    link2.config(state='normal')
    link1.pack()
    link2.pack()

    # Show the result text
    result.configure(text=result_text)


def open_abebooks():
    entry.get().strip().replace('-', '').replace(' ', '')
    isbn = re.sub(r'\D', '', entry.get())
    webbrowser.open(f'https://www.abebooks.com/servlet/SearchResults?kn={isbn}')


def open_bookfinder():
    entry.get().strip().replace('-', '').replace(' ', '')
    isbn = re.sub(r'\D', '', entry.get())
    webbrowser.open(f'https://www.bookfinder.com/isbn/{isbn}/')


if ui_mode:
    root = tk.Tk()
    root.title("Book Search")
    root.wm_attributes('-topmost', 1)  # always on top

    label = tk.Label(root, text="Enter an ISBN-10 or ISBN-13 code:")
    label.pack()

    entry = tk.Entry(root)
    entry.pack()
    entry.bind('<Return>', lambda event: search())

    button = tk.Button(root, text="Search", command=search)
    button.pack()

    result = tk.Label(root, text="")
    result.pack()

    link1 = tk.Button(root, text="Find on Abebooks", command=open_abebooks, state='normal')
    link2 = tk.Button(root, text="Find on Bookfinder", command=open_bookfinder, state='normal')

    root.mainloop()

else:

    def main():
        while True:
            error = False
            isbn = input("Enter an ISBN-10 or ISBN-13 code: ")
            isbn = isbn.replace('-', '').replace(' ', '')

            if len(isbn) not in [10, 13]:
                print(f"Error: ISBN must be 10 or 13 digits")
                error = True

            if len(isbn) == 10:
                isbn = convert_isbn10_to_isbn13(isbn)

            title, author, publisher, publication_year, ddc = get_info(isbn)
            best_new, best_used, destination = get_price(isbn)

            if not error:
                print(f"\n")
                print(f"Title: {title}")
                print(f"Author(s): {author}")
                print(f"ISBN-13: {isbn}")
                print(f"DDC: {ddc}")
                print(f"Publisher: {publisher}")
                print(f"Publication Year: {publication_year}")
                print(f"Open in Abebooks: https://www.abebooks.com/servlet/SearchResults?kn={isbn}")
                print(f"Open in Bookfinder: https://www.bookfinder.com/isbn/{isbn}")
                print(f"New Book Price: US$ {best_new}")
                print(f"Used Book Price: US$ {best_used}")
                print(f"Shipping To: {destination}")


    main()
