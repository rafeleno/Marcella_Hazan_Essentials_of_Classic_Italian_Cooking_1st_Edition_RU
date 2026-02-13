from bs4 import BeautifulSoup, NavigableString, Tag

html = '''
<p class="extract">
  <span class="color_CA4E00"><em>Note</em></span> 
  <img alt="" src="test.gif"/> 
  Some text after image.
</p>
'''

soup = BeautifulSoup(html, 'html.parser')

print("BEFORE:")
print(soup.prettify())

# Симулируем перевод (заменяем "Note" на "Примечание")
for text in soup.find_all(string=True):
    if "Note" in text:
        text.replace_with("Примечание")

print("\nAFTER:")
print(soup.prettify())
