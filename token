import nltk
from nltk.util import ngrams
from nltk.stem import WordNetLemmatizer,PorterStemmer
from nltk.tokenize import word_tokenize

nltk.download('punket')
nltk.download('punket_tab')
nltk.download('wordnet')

txt='i am dilip'
word=word_tokenize(txt)

wl=WordNetLemmatizer()
ps=PorterStemmer()

print('PorterStemmer',[ps.stem(word) for word in word])
print('WordNetLemmatizer',[wl.lemmatize(word) for word in word])

ug=list(ngrams(word,1))
bg=list(ngrams(word,2))
tg=list(ngrams(word,3))
print(ug)
print(bg)
print(tg)