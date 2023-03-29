from cataclysm import doom

def main():
    print("\nCataclysmic Hangman\n")
    guesses = []
    dead = False
    word = doom.randomly_select_word_for_hangman_game(wordlist=doom.get_hangman_complex_wordlist())
    while(not dead and not doom.hangman_word_is_guessed(word=word, guess_list=guesses)):
        doom.print_ascii_art_for_hangman(word=word, guess_list=guesses)
        letter_guess = doom.ask_user_for_hangman_letter_guess(guesses, allow_repeat_guesses=False)
        guesses.append(letter_guess)
        dead = doom.hangman_are_we_dead(word=word, guess_list=guesses)
    
    doom.print_ascii_art_for_hangman(word=word, guess_list=guesses)
    if doom.hangman_word_is_guessed(word=word, guess_list=guesses):
        print("You won!")
    else:
        print("You lost!")
    

if __name__ == '__main__':
    main()