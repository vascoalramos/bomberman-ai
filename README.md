# iia-ia-bomberman
Bomberman clone for AI teaching

![Demo](https://github.com/dgomes/iia-ia-bomberman/raw/master/data/DemoBomberman.gif)


## Description

This project is a product of the practical assignement of one of our classes: [Artifical Intelligence](https://www.ua.pt/en/uc/12287) and the main idea behind it is to implement an ai agent (using a* search algorithm) to win the bomberman game.


## How to install

Make sure you are running Python 3.5.

`$ pip install -r requirements.txt`

*Tip: you might want to create a virtualenv first*

## How to play

open 3 terminals:

`$ python3 server.py`

`$ python3 viewer.py`

`$ python3 client.py`

to play using the sample client make sure the client pygame hidden window has focus

### Keys

Directions: arrows

*A*: 'a' - detonates (only after picking up the detonator powerup)

*B*: 'b' - drops bomb

## Debug Installation

Make sure pygame is properly installed:

python -m pygame.examples.aliens

# Tested on:
- Ubuntu 18.04
- OSX 10.14.6
- Windows 10.0.18362

## Authors

* **Vasco Ramos:** [vascoalramos](https://github.com/vascoalramos)
* **Diogo Silva:** [HerouFenix](https://github.com/HerouFenix)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
