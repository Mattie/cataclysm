# Cataclysm - Last Library You'll Ever Use

## WORK IN PROGRESS

##  The End of Coding As We Know It
`cataclysm` doesn't care about code conventions and does whatever it thinks you want from context.

```python
>>> from cataclysm import consume
>>> consume(globals())

>>> print(longest_word_in_a_heading_on_the_bible_wikipedia_page())

```

## Installation (TODO)
```bash
pip install cataclysm
```

### Dependencies
* `python >= 3.8`
* `openai >= 0.2.5`
* `plunkylib >= 0.1.3`

### Configure API keys
Our demise is powered by OpenAI GPT4, so you'll need an API key from them.

Copy `.env.template` to `.env` in your working/app directory and add your API keys there:
```
OPENAI_API_KEY = "ADD_YOUR_OPENAI_KEY"
```

## Usage - Embracing the End
With a global cataclysm, fresh code will be generated for any unrecognized function anywhere. You just need a descriptive function name, arguments, and maybe some comments for context. The rest is up to fate.

```python
>>> from cataclysm import consume
>>> consume(globals())
>>> s = "May the gods have mercy on us all"
>>> corrupted = convert_some_words_to_disturbing_unicode_text(s, "mercy on us")
>>> print_surrounded_by_ascii_art_of_an_old_scroll(corrupted, use_wcwidth_for_padding=True)
 _________________________
| May the gods have m̜ͯ̂e͂ͦͥr̻̭͗c̳͖̍y̹̋̑  |
| o̵̰͒n̘͋͟ u̜͊ͤs̍͒͑ all                |
 ¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
```

```python
graph = {
    "A": {"B": 10, "C": 4},
    "B": {"A": 1, "C": 2, "D": 5},
    "C": {"A": 4, "B": 2, "D": 9},
    "D": {"B": 5, "C": 1},
}

# Don't have time to google the best module? Throw yourself headlong into eternity
shortest_path = find_shortest_path_dijkstra(graph, "A", "D")
print(f"Shortest path: {shortest_path}")
```
```
Shortest path: ['A', 'C', 'B', 'D']
```


## Safer Usage - Recommended
Mortals unable to endure a global cataclysm can use the `doom` module to limit their discomfort.

```python
>>> from cataclysm import doom
>>> uhoh = doom.first_prime_with_3_digits()
>>> print(uhoh)
101
```
