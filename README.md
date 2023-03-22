# Cataclysm - The Final Library

## WORK IN PROGRESS

##  End of Coding As We Know It
`cataclysm` doesn't care about mortal code conventions. It writes a function it thinks you need from context.

```python
>>> from cataclysm import consume
>>> consume(globals())

>>> x = get_italicized_phrases_wikipedia(page="Global catastrophic risk", only_lowercase_words=True, min_length=6)
>>> print(x[:5])
['existential risks', 'existential catastrophe[16]', 'global', 'terminal', 'permanent,']
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

## Usage - Global Cataclysm
With a global cataclysm, fresh code will be generated for any unrecognized function anywhere. You just need a descriptive function name, arguments, and maybe some comments for context. The rest is up to Them.

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
Or maybe you need harder problems removed...
```python
graph = {
    "A": {"B": 10, "C": 4},
    "B": {"A": 1, "C": 2, "D": 5},
    "C": {"A": 4, "B": 2, "D": 9},
    "D": {"B": 5, "C": 1},
}

# Don't have time to google a library? Throw yourself headlong into eternity:
shortest_path = find_shortest_path_dijkstra(graph, "A", "D")
print(f"Shortest path: {shortest_path}")
```
```
Shortest path: ['A', 'C', 'B', 'D']
```


## Usage - Doom (Recommended)
Mortals unable to endure a global cataclysm can succumb to their `doom` to reduce suffering.

```python
>>> from cataclysm import doom
>>> uhoh = doom.first_prime_with_3_digits()
>>> print(uhoh)
101
```
