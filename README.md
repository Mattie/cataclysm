# Cataclysm - End Game for Developers

##  Embrace the End
`cataclysm` is the end of mortal coding. Let inhuman intelligence write your code based on context.

```python
>>> from cataclysm import consume
>>> consume(globals())

>>> x = get_italicized_phrases_wikipedia(page="Global catastrophic risk", only_lowercase_words=True, min_length=6)
>>> print(x[:5])
['existential risks', 'existential catastrophe[16]', 'global', 'terminal', 'permanent,']
```

## Installation
```bash
pip install cataclysm

# in your project directory, copy the default datafiles
cataclysm init
```

### Configure API keys
Our demise is powered by OpenAI GPT4, so you'll need an API key from them.

Use `init` or copy `env.template.cataclysm` to `.env` in your working/app directory and add your API keys there:
```
OPENAI_API_KEY = "ADD_YOUR_OPENAI_KEY"
```

## Usage (Modes)
### Global Cataclysm
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
Or maybe you wish to channel the energies to solve harder problems...
```python
graph = {
    "A": {"B": 10, "C": 4},
    "B": {"A": 1, "C": 2, "D": 5},
    "C": {"A": 4, "B": 2, "D": 9},
    "D": {"B": 5, "C": 1},
}

# Why google it when you can throw yourself headlong into eternity?
shortest_path = find_shortest_path_dijkstra(graph, "A", "D")
print(f"Shortest path: {shortest_path}")
```
> `Shortest path: ['A', 'C', 'B', 'D']`

While `consume()` can be used for experimental purposes in notebooks and in interactive modes, it's not designed to be used in libraries or apps. If you'd like to experiment, consume() is great, but you'll need the `doom` module to make an app cataclysmic.

### **Doom** (Recommended)
Mortals unwilling to face a global cataclysm can face their `doom` instead. Recommended if you wish to use these powers in libraries or apps.

```python
>>> from cataclysm import doom
>>> uhoh = doom.first_prime_with_3_digits()
>>> print(uhoh)
101
```

### **Impending Doom** (Preview Mode)
If you fear a `cataclysm`, your impending doom can be generated and previewed via `doom.impending`.

```python
>>> from cataclysm import doom
>>> dump_unexecuted_code_str = doom.impending.say_stuff("YOU ARE DOOMED")
>>> print(dump_unexecuted_code_str)
[... code dump ...]
```

### **Chosen Doom** (Frozen Mode)
If you've chosen your own `doom`, you can  impending doom can be generated and previewed via `doom.impending`.

```python
>>> from cataclysm import doom
>>> dump_unexecuted_code_str = doom.impending.say_stuff("YOU ARE DOOMED")
>>> print(dump_unexecuted_code_str)
[... code dump ...]
```

## Useful Resources and Examples

* [Youtube Overview](https://youtu.be/ZK8fUuQDgZ4)
* [Notebook - Getting Started With The End](notebooks/GettingStartedWithTheEnd-cataclysm.ipynb)
* [Example Apps](examples/)
* [Tests](tests/)


## Frequently Asked Questions (FAQ)

### Is `cataclysm` safe?

> That's not the word I would use. The library name should give you a hint, but to be explicit:

**WARNING: The `cataclysm` could destroy you and everything you hold dear. If you proceed, you face your `doom` alone-- no one else can be blamed for your folly.**

### Sounds scary, but isn't `cataclysm` the future of coding?

> While GPT4 has never done anything wrong to me (as reckless as I am trusting its code), this is a dangerous and mysterious power that only the maddest of mortals should wield. There are great, dark powers beyond our comprehension at work. Alien minds are not to be trifled with.
> 
> The prompt(s) used for `doom` intentionally discourage the LLM from using any local I/O except where it is explicitly sought. Yet it could be tricked, confused, misled, or gain an unexpected hunger for destruction. You have been warned.
> 
> *I personally see AI-generated code a lot like how GPS was initially-- following it blindly will sometimes lead you to drive into a lake. Yet, over the years, many of us depend on GPS every day and wouldn't drive anywhere without it. I put Codex and GPT 3.5 (original ChatGPT) in the former camp. GPT4+ is really impressive thus far, but not without dangerous quirks.*

### How do I access the `cataclysm`?

> You'll need the `cataclysm` from PyPI-- install it via `pip install cataclysm`.

### What forces are at work to bring about `cataclysm`?

>  The devastation is powered by OpenAI's ChatGPT API for the `gpt-4` large language model (LLM). It also works with  `gpt-3.5-turbo`, but GPT4+ is highly recommended. The API is called via `plunkylib` (a yaml-friendly layer not totally unlike `langchain`), so you need an OpenAI API key. Include your own API key in your `.env` file, using `.env.template` as a reference.

### Can I experiment with a weaker `cataclysm` using `gpt-3.5-turbo`?

>  To do so, edit `datafiles/plunkylib/petitions/CataclysmQuery.yml` to reference `CataclysmLLMParams_3-5` instead of `CataclysmLLMParams`. Your doom will be less impressive, but faster and less expensive.

### What if I don't have an OpenAI account or API key?

> I'm considering ways to grow the `cataclysm` to enhance code generation via a more powerful hosted API. Reach out if you would be interested in this.

### Does it call OpenAI constantly? That seems excessive.

> Those dark powers are tempting to use, but `cataclysm` locally caches code created for each function signature. The second+ time it is called, the cached code is used-- so it'll be a lot faster. It's recommended that if you are insane enough to ship code using `cataclysm` that you ship the code files. If you wish to `doom` generation, you can use `doom.chosen` to ensure the released code never tries to generate any code. If you want to look at the code for a generation, they typically live in `./datafiles/cataclysm/code/<functionname>.yml` or can be previewed with `doom.impending`.
> 
> Note that when code is first generated and exec'd, if there is an error raised, it will re-generate the code one more time and try again. If it fails then, you've stumped the AI and you may need to provide more guidance (or install more modules).

### What fate awaits me if I choose `cataclysm`+`consume()` over `doom`?

> Embracing `cataclysm` consumes globals(), letting any unrecognized function unleash AI-generated code. `doom`, however, demands explicit invocation, granting you some illusion of control of your fate.

### Can `cataclysm`/`doom` really code anything?

> It's pretty good at doing simple things and surprisingly decent at doing complex things. You will have to explore the `cataclysm` to understand its limitations. You can see some working examples in the `notebooks` folder, `examples` folder and some tests in the `tests` folder.
> I'm experimenting with a mode that allows `cataclysm` to recursively use itself to generate code. This path is a scary one, but may be even more impressive.

### How do I peer into the impending `doom` without unleashing it?

> With `doom.impending`, you can glimpse into the abyss without invoking the new code. This is ideal for those who want to learn how it behaves in response to changes in comments, keyword arguments, docstrings, modules, and function signatures.

### What does `cataclysm` inspect to make its decisions on what to code?

> As of now it looks at your function signatures, call stacks, keyword argument names, docstrings, and even comments to mold the code to serve your mortal wishes. See the notebooks, examples, and tests for reference.

### Can we predict the `cataclysm`? Is the code-generation deterministic / repeatable?

> Once code has been generated for a given function and arguments, it will default to using the generated code every time. So it'll run predictably. You can guarantee that using `doom.chosen`, if you'd like. 
> When it comes to code generation, in theory, `cataclysm` can regenerate the same code, but only if the callstack is the same, as well as the function name, arguments, installed modules, etc. (basically if it's the same exact function call + context). In practice, you will find it difficult to get the exact same code twice, so it's best to use the cached code (or `.chosen`) if you want to be sure.

### What prompts are you using? Can I change the prompts used? 

> The prompts are in `default_files/datafiles/plunkylib/prompts/`. These will be changing a lot in the early days of the `cataclysm`, but you are free to experiment on your own. All I ask is that you consider sharing your coolest findings back to the project.

### Can you help my company use generative AI for our software development?

> If you're seeking less cataclysmic ways to wield these dark powers, reach out to Mattie (email format: `username@username.ai`). I'm happy to explore options for helping your company's developers embrace the new reality.
