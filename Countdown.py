import string
import random
import itertools
import time
import math
import threading
import multiprocessing
from functools import partial
import queue
from subprocess import check_output

if __name__ == '__main__':  # only show hello pygame for main thread (not multiprocessing threads)
    import pygame
else:
    import contextlib
    with contextlib.redirect_stdout(None):  # dont output to log
        import pygame

BLACK = (0, 0, 0)
GREY = (128, 128, 128)
LIGHT_GREY = (210, 210, 210)
WHITE = (255, 255, 255)
BLUE = (217, 231, 249)
DARK_BLUE = (0, 0, 255)
debug = False           # adds target number to available numbers in numbers game
MULTITHREADING = True   # Selects whether to use multithreading with the python implementation of the numbers solver
PYTHON_SOLVER = False    # Selects using the python or c implementation of the numbers solver

# NOTE:  all of the 'variable defined outside of __init__' errors are
# due to using self.__dict__[variable] in order to avoid calling __setattr__


class textBox(pygame.sprite.Sprite):
    def __init__(self, x, y, text, size_x=200, size_y=60, dynamicSize=False, colour=BLACK):
        super().__init__()

        self.size_x = size_x
        self.size_y = size_y
        self.colour = colour

        self.image = pygame.Surface([size_x, size_y])

        self.rect = self.image.get_rect()

        self.posCenter = [x, y]

        self.dynamicSize = dynamicSize
        self.text = text

    def __setattr__(self, name, value):  # Check changed variable is valid
        if name == 'text':
            self.__dict__[name] = value

            self.tileText = myFont.render(str(self.text), 1, self.colour)

            textWidth = self.tileText.get_width()
            textHeight = self.tileText.get_height()

            if self.dynamicSize and textWidth * 1.05 > self.size_x:  # If text doesnt fit, make it bigger
                self.size_x = textWidth * 1.05
                self.image = pygame.Surface([self.size_x, self.size_y])

                self.rect = self.image.get_rect()
                self.rect.center = self.posCenter

            self.image.fill(WHITE)

            self.image.blit(self.tileText, [self.size_x / 2 - textWidth / 2, self.size_y / 2 - textHeight / 2])

        elif name == 'posCenter':
            self.__dict__['posCenter'] = value
            self.rect.center = self.posCenter

        else:
            super().__setattr__(name, value)


class inputBox(textBox):
    def __init__(self, x, y, size_x=200, size_y=60, defaultText='', validInput=string.ascii_lowercase + string.digits, maxChars=0, dynamicSize=False, selectable=True):
        self.maxChars = maxChars

        super().__init__(x=x, y=y, text=defaultText, size_x=size_x, size_y=size_y, dynamicSize=dynamicSize, colour=GREY)

        self.validInput = validInput
        self.__dict__['selectable'] = selectable  # set selected to false without calling __setattr__

        self.__dict__['selected'] = False

        self.lastTime = time.time()
        self.__dict__['cursorVisible'] = False
        self.__dict__['cursorPosition'] = 0  # position from end
        self.cursorCounter = 0

        self.defaultText = defaultText
        self.__dict__['text'] = ''
        self.text = ''

        self.result = 0

    def update(self, events=()):
        if self.selected:
            self.cursorCounter += time.time() - self.lastTime
            self.lastTime = time.time()
            if self.cursorCounter > 0.5:
                self.cursorCounter = 0
                self.cursorVisible = not self.cursorVisible

        for event in events:
            if self.selected:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:  # move cursor
                        self.cursorPosition += 1
                    elif event.key == pygame.K_RIGHT:
                        self.cursorPosition -= 1

                    elif event.key == pygame.K_BACKSPACE:  # delete character before cursor
                        self.cursorCounter = 0
                        self.cursorVisible = True

                        if self.cursorPosition == 0:
                            self.text = self.text[:-1]
                        else:
                            self.text = self.text[:-self.cursorPosition - 1] + self.text[-self.cursorPosition:]

                    elif event.unicode in self.validInput:  # if character is valid, add it before cursor
                        self.colour = BLACK
                        if self.cursorPosition == 0:
                            self.text += event.unicode
                        else:
                            self.text = self.text[:-self.cursorPosition] + event.unicode + self.text[-self.cursorPosition:]

            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.rect.collidepoint(mouseTransform(pygame.mouse.get_pos())):
                    self.selected = True
                else:
                    self.selected = False

    def placeCursor(self):  # Add cursor to the text
        if self.cursorPosition == 0:
            if self.cursorVisible:
                output = self.text + "|"
            else:
                output = self.text + " "
        else:
            if self.cursorVisible:
                output = self.text[:-self.cursorPosition] + "|" + self.text[-self.cursorPosition:]
            else:
                output = self.text[:-self.cursorPosition] + " " + self.text[-self.cursorPosition:]

        return output

    def __setattr__(self, name, value):  # Check changed variable is valid
        if name == 'text':
            if self.maxChars == 0 or len(value) <= self.maxChars:  # max chars=0 means unlimited characters
                if value == '':  # Display default text
                    self.__dict__['text'] = value

                    self.image.fill(WHITE)
                    if not self.selected:
                        self.tileText = myFont.render(str(self.defaultText), 1, GREY)

                        textWidth = self.tileText.get_width()
                        textHeight = self.tileText.get_height()
                        if self.dynamicSize and textWidth * 1.05 > self.size_x:  # make text larger if default text is too long
                            self.size_x = textWidth * 1.05
                            self.image = pygame.Surface([self.size_x, self.size_y])
                            self.image.fill(WHITE)

                            self.rect = self.image.get_rect()
                            self.rect.center = self.posCenter

                        self.image.blit(self.tileText, [self.size_x / 2 - textWidth / 2, self.size_y / 2 - textHeight / 2])
                    else:
                        super().__setattr__(name, value)
                else:
                    #self.colour = BLACK  ######CHANGED HERE
                    super().__setattr__(name, value)
        elif name == 'selected':
            if self.selectable:
                self.__dict__['selected'] = value

                self.cursorCounter = 0  # reset the cursor flashing timer
                self.cursorVisible = False  # show the cursor

                self.image.fill(WHITE)
                if self.text == '' and not self.selected:
                    self.tileText = myFont.render(str(self.defaultText), 1, GREY)
                else:
                    self.tileText = myFont.render(self.placeCursor(), 1, BLACK)

                textWidth = self.tileText.get_width()
                textHeight = self.tileText.get_height()
                self.image.blit(self.tileText, [self.size_x / 2 - textWidth / 2, self.size_y / 2 - textHeight / 2])  # add text to the middle of the text box

        elif name == 'cursorVisible':
            self.__dict__['cursorVisible'] = value

            self.image.fill(WHITE)
            self.tileText = myFont.render(self.placeCursor(), 1, BLACK)  # add the cursor

            textWidth = self.tileText.get_width()
            textHeight = self.tileText.get_height()
            self.image.blit(self.tileText, [self.size_x / 2 - textWidth / 2, self.size_y / 2 - textHeight / 2])  # render cursor

        elif name == 'cursorPosition':
            if 0 <= value <= len(self.text):  # only allowed to be between 0 and the length of the text
                self.__dict__['cursorPosition'] = value

        elif name == 'selectable':  # disable the input functionality
            self.cursorPosition = 0
            self.cursorVisible = False
            self.selected = False
            self.__dict__['selectable'] = value

        else:
            super().__setattr__(name, value)


class gameManager:
    def __init__(self):
        # Initialize variables
        self.gameType = ""
        self.nPlayers = 0

        self.scoreBoard1 = textBox
        self.scoreBoard2 = textBox

        self.player1Score = 0
        self.player2Score = 0

        self.player1Solution = ''
        self.player2Solution = ''

        self.player1Target = 0
        self.player2Target = 0

    def __setattr__(self, name, value):
        if name == 'player1Score':
            self.__dict__['player1Score'] = value
            if self.gameType == "All":
                self.scoreBoard1.text = self.player1Score

        elif name == 'player2Score':
            self.__dict__['player2Score'] = value
            if self.gameType == "All":
                self.scoreBoard2.text = self.player2Score

        else:
            super().__setattr__(name, value)


class timer(pygame.sprite.Sprite):
    def __init__(self, x, y, size_x, size_y):
        super().__init__()

        self.image = pygame.Surface([size_x, size_y])
        self.image.fill(WHITE)

        self.size_x = size_x
        self.size_y = size_y
        self.running = True
        self.counter = 30  # current progress
        self.lastTime = time.time()

        self.rect = self.image.get_rect()
        self.centerPos = [x, y]
        self.rect.center = self.centerPos
        pygame.mixer_music.load("Countdown - Clock Only short.mp3")
        pygame.mixer_music.play(1)

    def update(self, events=()):
        if self.running:
            self.counter = self.counter - (time.time() - self.lastTime)  # remove delta time since last subtraction
            self.lastTime = time.time()

    def __setattr__(self, name, value):
        if name == 'counter':
            self.__dict__[name] = value
            if self.counter >= 0:
                self.progressBar = pygame.Surface([(self.size_x - 10) * ((30 - self.counter) / 30), self.size_y - 10])
                self.progressBar.fill(DARK_BLUE)
                self.image.fill(LIGHT_GREY)
                self.image.blit(self.progressBar, [5, 5])
        else:
            super().__setattr__(name, value)


def mouseTransform(mousePos):
    output = [mousePos[0]*1920/Screen.get_width(), mousePos[1]*1080/Screen.get_height()]
    return output


def draw(listToDraw):  # Draw the new screen using listToDraw
    # Draw sprites
    listToDraw.draw(renderScreen)

    # scale it to the current resolution being used
    pygame.transform.scale(renderScreen, (Screen.get_width(), Screen.get_height()), Screen)

    # new screen
    pygame.display.flip()

    # Clear screen
    # redraw the background
    renderScreen.fill(BLUE)

    # Pause to have same FPS
    clock.tick(60)


def checkExit(events):  # Check for escape/close button
    for event in events:
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit()
            quit()


def selectGameMode():  # Initial selection screen
    singlePlayerButton = textBox(850, 300, "1 player", dynamicSize=True)  # how many players
    buttonList.add(singlePlayerButton)
    activeSpriteList.add(singlePlayerButton)
    allSpriteList.add(singlePlayerButton)

    twoPlayerButton = textBox(1070, 300, "2 player", dynamicSize=True)
    buttonList.add(twoPlayerButton)
    activeSpriteList.add(twoPlayerButton)
    allSpriteList.add(twoPlayerButton)

    exitButton = textBox(Screen.get_width() / 2, 900, "Exit", dynamicSize=True)
    buttonList.add(exitButton)
    activeSpriteList.add(exitButton)
    allSpriteList.add(exitButton)

    game.nPlayers = 0

    while game.nPlayers == 0:
        events = pygame.event.get()
        checkExit(events)
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                for sprite in buttonList:
                    if sprite.rect.collidepoint(mouseTransform(pygame.mouse.get_pos())):
                        for button in buttonList:
                            button.kill()

                        if sprite == singlePlayerButton:
                            game.nPlayers = 1

                        elif sprite == twoPlayerButton:
                            game.nPlayers = 2

                        elif sprite == exitButton:
                            pygame.quit()
                            quit()

        allSpriteList.update(events)

        draw(allSpriteList)

    for button in buttonList:  # kill buttons
        button.kill()

    fullGameButton = textBox(500, 300, "Play all rounds", dynamicSize=True)  # select game mode
    buttonList.add(fullGameButton)
    activeSpriteList.add(fullGameButton)
    allSpriteList.add(fullGameButton)

    letterButton = textBox(960, 300, "Play the letters game", dynamicSize=True)
    buttonList.add(letterButton)
    activeSpriteList.add(letterButton)
    allSpriteList.add(letterButton)

    numberButton = textBox(1420, 300, "Play the numbers game", dynamicSize=True)
    buttonList.add(numberButton)
    activeSpriteList.add(numberButton)
    allSpriteList.add(numberButton)

    gameSelected = False
    while not gameSelected:
        events = pygame.event.get()
        checkExit(events)
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                for sprite in buttonList:
                    if sprite.rect.collidepoint(mouseTransform(pygame.mouse.get_pos())):
                        for button in buttonList:
                            button.kill()

                        if sprite == numberButton:
                            return "Number"

                        elif sprite == letterButton:
                            return "Letter"

                        elif sprite == fullGameButton:
                            return "All"

        allSpriteList.update(events)

        draw(allSpriteList)


def evaluate(userInput, tileNumbers, targetNumberBox, userTarget, feedback):
    try:  # evaluate the string input
        result = eval(userInput.text)
    except SyntaxError:
        feedback.text = "Unable to evaluate"
        return 0  # give 0 points

    expression = userInput.text
    numbers = []
    currentNumber = ""
    feedbackText = "Correct"
    allNumberExist = True
    validSolution = True

    userInput.text += " = " + str(result)

    for j in range(len(expression)):  # find numbers used as list (numbers)
        char = expression[j]
        if char in string.digits + "+-*/() ":
            if char in string.digits:
                currentNumber += char
            elif not currentNumber == '':
                numbers.append(currentNumber)
                currentNumber = ""

            if len(expression) == j + 1 and not currentNumber == '':  # write last one
                numbers.append(currentNumber)

    if result == userTarget:  # Same as user said they got
        tilesAvailable = tileNumbers.copy()
        for number in numbers:
            if int(number) in tilesAvailable:  # check all numbers are available (and enough of each)
                tilesAvailable.remove(int(number))
            else:
                print("Extra number:", number)
                feedbackText = "You used extra numbers"
                feedback.text = feedbackText
                return 0

        if not result == targetNumberBox.text:  # answer not correct
            feedbackText = "You are " + str(abs(result - int(targetNumberBox.text))) + " away"
            validSolution = False

        feedback.text = feedbackText
        if validSolution:  # score the game
            return 10
        elif allNumberExist:
            if abs(result - int(targetNumberBox.text)) <= 5:
                return 7
            elif abs(result - int(targetNumberBox.text)) <= 10:
                return 5
    else:
        feedbackText = "Not the same as you originally got"
        feedback.text = feedbackText
        return 0

    feedback.text = feedbackText

    print(userInput.text + " = " + str(result))

    return 0


##############################
# Solve number game
def evalRPN(oldList, ops):  # evaluate a list as Reverse polish notation
    listToEval = oldList.copy()
    i = 2
    j = len(listToEval)  # keep track of length of the list, faster than calling len(listToEval) every time
    while j > 1:
        element = listToEval[i]
        if element in ops:  # if element is an operator
            prev = listToEval.pop(i - 2)  # remove both numbers
            prev2 = listToEval.pop(i - 2)
            i -= 2
            j -= 2
            if element == "+":  # find the operator and do the operation
                result = prev + prev2
            elif element == "-":
                result = prev - prev2
            elif element == "*":
                result = prev * prev2
            else:
                result = prev / prev2

            # if it is a valid sum, replace the operator with the result
            if 0 >= result or not int(result) == result or result == prev or result == prev2:
                return -1
            else:
                listToEval[i] = int(result)

        i += 1

    return listToEval[0]  # return the only value left in the list


def isValidRPN(listRPN, nOps, ops):
    listToEval = list(listRPN)
    i = 2
    j = nOps  # how many times the function needs to run
    while j > 0:
        element = listToEval[i]
        if element in ops:
            prev = listToEval.pop(i - 2)
            prev2 = listToEval.pop(i - 2)
            i -= 2
            j -= 1
            if element == "+":
                result = prev + prev2
            elif element == "-":
                result = prev - prev2
            elif element == "*":
                result = prev * prev2
            else:
                result = prev / prev2

            if 0 >= result or not int(result) == result or result == prev or result == prev2:
                return False  # current RPN is invalid/not usefull
            else:
                listToEval[i] = int(result)

        i += 1

    return True


def generateRPN(nNums, nOps, level, targetNumber, solutions, ops, args):  # currentList = args[0]  remNums = args[1]
    if isValidRPN(args[0], nOps, ops):  # check current RPN is valid
        if level == 11:  # final level, 6 numbers with 5 operators
            result = evalRPN(args[0], ops)
            if abs(result - targetNumber) <= 10:  # if less than 10 away
                solutions.put((args[0], abs(result - targetNumber)))  # add solution to queue for later retrieval
            return
        if nNums - nOps == 1:  # valid RPN function
            result = evalRPN(args[0], ops)

            if abs(result - targetNumber) <= 10:
                solutions.put((args[0], abs(result - targetNumber)))

            for i in args[1]:  # for each number not used yet
                newList = []
                newList.extend(args[0])
                remNums = args[1].copy()  # copy array, dont use array pointer
                newList.append(remNums.pop(remNums.index(i)))
                generateRPN(nNums + 1, nOps, level + 1, targetNumber, solutions, ops, (newList, remNums))

        elif nNums == 6:  # once all numbers reached
            for i in ["+", "-", "*", "/"]:
                newList = []
                newList.extend(args[0])
                newList.append(i)
                generateRPN(nNums, nOps + 1, level + 1, targetNumber, solutions, ops, (newList, args[1]))
        else:
            for i in ["+", "-", "*", "/"]:  # add operators
                newList = []
                newList.extend(args[0])
                newList.append(i)
                remNums = args[1].copy()
                generateRPN(nNums, nOps + 1, level + 1, targetNumber, solutions, ops, (newList, remNums))

            for i in args[1]:  # add numbers
                newList = []
                newList.extend(args[0])
                remNums = []
                remNums.extend(args[1])
                newList.append(remNums.pop(remNums.index(i)))
                generateRPN(nNums + 1, nOps, level + 1, targetNumber, solutions, ops, (newList, remNums))
    else:
        return


def convertRPNToEnglish(polishNotation):  # convert a list of RPN to seperate 'normal' sums
    newList = []
    newList.extend(polishNotation)
    outputSums = []
    ops = ["+", "-", "*", "/"]
    i = 2
    while len(newList) > 1:
        element = newList[i]
        if element in ops:
            prev = newList.pop(i - 2)
            prev2 = newList.pop(i - 2)
            i = i - 2

            result = str(prev) + element + str(prev2)

            outputSums.append(result + "=" + str(int(eval(result))))

            newList[i] = int(eval(result))

        i += 1

    return outputSums


def findSolution(numberList, targetNumber, outputQueue):
    print("Starting number solver")
    if PYTHON_SOLVER:
        startTime = time.time()  # used for timing

        ops = {"+", "-", "*", "/"}

        numberOrder = itertools.permutations(numberList, 2)

        arguments = []
        for order in numberOrder:
            tempList = []
            tempList.extend(numberList)
            tempList.remove(order[0])
            tempList.remove(order[1])
            arguments.append((order, tempList))  # add tuple of first 2 numbers and the remaining numbers
            print(tempList, order)


        if multiprocessing.cpu_count() >= 3 and MULTITHREADING:  # ensure enough CPU cores are available
            print("Using multiprocessing")
            queueOut = multiprocessing.Manager().Queue()  # Queue for returning answers from multiple threads

            func = partial(generateRPN, 2, 0, 2, targetNumber, queueOut, ops)  # fixed variables

            myPool = multiprocessing.Pool(processes=multiprocessing.cpu_count() - 1)

            myPool.map(func, arguments)
        else:
            print("Using single thread")
            queueOut = queue.Queue()
            for arg in arguments:  # don't use multiprocessing if only 1 or 2 cores are available
                generateRPN(2, 0, 2, targetNumber, queueOut, ops, arg)

        # Retrieve solutions from the queue
        solutions = []
        while not queueOut.empty():
            solutions.append(queueOut.get())

        solutions.sort(key=lambda x: (x[1], len(x[0])))  # sort the solutions

        for solution in solutions:  # print all closest answers to debug log
            if solution[1] == solutions[0][1]:
                print(convertRPNToEnglish(solution[0]))

        outputSolution = convertRPNToEnglish(solutions[0][0])  # output solution as list of sums

        print(time.time() - startTime)  # print time taken

        print(outputSolution)  # shortest solution
        outputQueue.put(outputSolution)  # send solution to main thread

    else:
        argument = "rpn.exe " + str(targetNumber) + " "
        for number in numberList:
            argument += str(number) + " "
        print(argument)

        #os.system(argument)
        shellOutput = check_output(argument, shell=True)

        print(shellOutput)

        output = str(shellOutput)[2:].split("\\n")

        for lineNo in range(len(output)):
            line = output[lineNo]
            output[lineNo] = line.rstrip()[:-2]
            print(output[lineNo])
        outputSolution = output[:-3]
    outputQueue.put(outputSolution)
    print(outputSolution)
#
##############################


def playNumbersGame():
    print("Starting numbers game")

    # create sprites
    posSmallNumbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]  # small numbers available
    posLargeNumbers = [25, 50, 75, 100]  # large number available

    largeSelection = 0
    # how many large and small numbers?
    questionBox = textBox(renderScreen.get_width() / 2, 200, "Choose 1, 2, 3 or 4 large numbers", dynamicSize=True)
    activeSpriteList.add(questionBox)
    allSpriteList.add(questionBox)

    howManyNumbers = inputBox(renderScreen.get_width() / 2, 500, size_x=300, defaultText="How many large numbers?", validInput=["1", "2", "3", "4"], maxChars=1)
    activeSpriteList.add(howManyNumbers)
    allSpriteList.add(howManyNumbers)

    while not 1 <= largeSelection <= 4:  # wait until large selection has been set
        events = pygame.event.get()
        checkExit(events)
        for event in events:
            if event.type == pygame.KEYDOWN and (event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER) and len(howManyNumbers.text) > 0:
                largeSelection = int(howManyNumbers.text)
                break
        allSpriteList.update(events)

        draw(allSpriteList)

    for sprite in activeSpriteList:
        sprite.kill()

    # list of all tiles
    tileNumbers = []

    # small numbers
    for i in range(6 - largeSelection):
        randNo = random.randint(0, len(posSmallNumbers) - 1)
        tileNumbers.append(posSmallNumbers[randNo])
        currentTile = textBox(renderScreen.get_width() / 2 - 187 + 75 * i, 400, posSmallNumbers.pop(randNo), size_x=60, size_y=60)
        tileList.add(currentTile)
        activeSpriteList.add(currentTile)
        allSpriteList.add(currentTile)

    # large numbers
    for i in range(largeSelection):
        randNo = random.randint(0, len(posLargeNumbers) - 1)
        tileNumbers.append(posLargeNumbers[randNo])
        currentTile = textBox(renderScreen.get_width() / 2 - 187 + 75 * (i + 6 - largeSelection), 400, posLargeNumbers.pop(randNo), size_x=60, size_y=60)
        tileList.add(currentTile)
        activeSpriteList.add(currentTile)
        allSpriteList.add(currentTile)

    if game.nPlayers == 1:
        userInput = inputBox(renderScreen.get_width() / 2, 600, size_x=240, defaultText="What is your answer?", validInput=string.digits, dynamicSize=True, maxChars=35)
        activeSpriteList.add(userInput)
        allSpriteList.add(userInput)

    targetNumberBox = textBox(renderScreen.get_width() / 2, 200, random.randint(100, 999))
    activeSpriteList.add(targetNumberBox)
    allSpriteList.add(targetNumberBox)

    countdownClock = timer(renderScreen.get_width() / 2, 800, 1500, 50)
    activeSpriteList.add(countdownClock)
    allSpriteList.add(countdownClock)

    # setup and start background process
    returnQueue = queue.Queue()
    workerThread = threading.Thread(target=findSolution, args=(tileNumbers, int(targetNumberBox.text), returnQueue))
    workerThread.daemon = True
    workerThread.start()

    # to make the game easier, add the target number to the list of available numbers
    if debug:
        tileNumbers.append(int(targetNumberBox.text))

    while countdownClock.counter >= 0:  # wait for timer
        events = pygame.event.get()
        checkExit(events)

        allSpriteList.update(events)

        draw(allSpriteList)

    countdownClock.running = False

    # Take initial answers
    if game.nPlayers == 2:
        ##########
        # player 1
        userInput = inputBox(renderScreen.get_width() / 2, 600, size_x=240, defaultText="Player 1 answer?", validInput=string.digits, dynamicSize=True, maxChars=35)
        activeSpriteList.add(userInput)
        allSpriteList.add(userInput)

        done = False
        while not done:  # while waiting for timer
            events = pygame.event.get()
            checkExit(events)

            for event in events:
                if event.type == pygame.KEYDOWN and (event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER and len(userInput.text) > 0):
                    done = True
                    break

            allSpriteList.update(events)

            draw(allSpriteList)

        if len(userInput.text) > 0:
            game.player1Target = int(userInput.text)
        else:
            game.player1Target = 0
        userInput.kill()

        ##########
        # player 2
        userInput = inputBox(renderScreen.get_width() / 2, 600, size_x=240, defaultText="Player 2 answer?", validInput=string.digits, dynamicSize=True, maxChars=35)
        activeSpriteList.add(userInput)
        allSpriteList.add(userInput)

        done = False
        while not done:  # while waiting for timer
            events = pygame.event.get()
            checkExit(events)

            for event in events:
                if event.type == pygame.KEYDOWN and (event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER) and len(userInput.text) > 0:
                    done = True
                    break

            allSpriteList.update(events)

            draw(allSpriteList)

        if len(userInput.text) > 0:
            game.player2Target = int(userInput.text)
        else:
            game.player2Target = 0
        userInput.kill()
        ##########
    else:
        ##########
        # single player
        if len(userInput.text) > 0:
            userTarget = int(userInput.text)
        else:
            userTarget = 0
        userInput.kill()
        ##########

    # Get solutions
    if game.nPlayers == 2:
        ##########
        # player 1
        userInput = inputBox(renderScreen.get_width() / 2, 600, size_x=240, defaultText="How did you get to " + str(game.player1Target) + " player 1?", validInput=string.digits + "+-/*()", dynamicSize=True, maxChars=35)
        activeSpriteList.add(userInput)
        allSpriteList.add(userInput)

        done = False
        while not done:  # while waiting for user
            events = pygame.event.get()
            checkExit(events)

            for event in events:
                if event.type == pygame.KEYDOWN and (event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER) and len(userInput.text) > 0:
                    done = True
                    break

            allSpriteList.update(events)

            draw(allSpriteList)

        game.player1Solution = userInput.text

        player1Answer = textBox(renderScreen.get_width() / 2, 500, game.player1Solution, size_x=240, dynamicSize=True)
        activeSpriteList.add(player1Answer)
        allSpriteList.add(player1Answer)

        userInput.kill()

        ##########
        # player 2
        userInput = inputBox(renderScreen.get_width() / 2, 600, size_x=240, defaultText="How did you get to " + str(game.player2Target) + " player 2?", validInput=string.digits + "+-/*()", dynamicSize=True, maxChars=35)
        activeSpriteList.add(userInput)
        allSpriteList.add(userInput)

        done = False
        while not done:  # while waiting for user
            events = pygame.event.get()
            checkExit(events)

            for event in events:
                if event.type == pygame.KEYDOWN and (event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER) and len(userInput.text) > 0:
                    done = True
                    break

            allSpriteList.update(events)

            draw(allSpriteList)

        game.player2Solution = userInput.text

        player2Answer = textBox(renderScreen.get_width() / 2, 600, game.player2Solution, size_x=240, dynamicSize=True)
        activeSpriteList.add(player2Answer)
        allSpriteList.add(player2Answer)

        feedback = textBox(300, 500, "", size_x=300)
        activeSpriteList.add(feedback)
        allSpriteList.add(feedback)

        feedback2 = textBox(300, 600, "", size_x=300)
        activeSpriteList.add(feedback2)
        allSpriteList.add(feedback2)

        player1Delta = evaluate(player1Answer, tileNumbers, targetNumberBox, game.player1Target, feedback)
        player2Delta = evaluate(player2Answer, tileNumbers, targetNumberBox, game.player2Target, feedback2)

        if player1Delta == player2Delta:  # if same number of points, both, otherwise only highest scorer gains their points
            game.player1Score += player1Delta
            game.player2Score += player2Delta
        elif player1Delta > player2Delta:
            game.player1Score += player1Delta
        elif player2Delta > player1Delta:
            game.player2Score += player2Delta

        userInput.kill()
        ##########
    else:
        ##########
        # single player
        userInput = inputBox(renderScreen.get_width() / 2, 600, size_x=240, defaultText="How did you get to " + str(userTarget) + "?", validInput=string.digits + "+-/*()", dynamicSize=True, maxChars=35)
        allSpriteList.add(userInput)
        activeSpriteList.add(userInput)

        done = False
        while not done:
            events = pygame.event.get()
            checkExit(events)

            allSpriteList.update(events)

            for event in events:
                if event.type == pygame.KEYDOWN and (event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER) and len(userInput.text) > 0:  # wait for user to enter their solution
                    done = True
                    feedback = textBox(300, 600, "", size_x=300)
                    activeSpriteList.add(feedback)
                    allSpriteList.add(feedback)

                    game.player1Score += evaluate(userInput, tileNumbers, targetNumberBox, userTarget, feedback)
                    break

            draw(allSpriteList)

    userInput.selectable = False

    feedbackList = pygame.sprite.Group()  # list used to display sums

    titleTextbox = textBox(1450, 125, "Please wait", size_x=200, dynamicSize=True)
    feedbackList.add(titleTextbox)
    activeSpriteList.add(titleTextbox)
    allSpriteList.add(titleTextbox)

    while workerThread.isAlive():  # ensure the solution thread has finished
        events = pygame.event.get()

        checkExit(events)

        allSpriteList.update(events)

        draw(allSpriteList)

    answer = returnQueue.get()  # get the solution
    titleTextbox.text = "Shortest solution"

    for i in range(len(answer)):  # display solution
        tempTextbox = textBox(1450, 200 + 60 * i, answer[i])
        feedbackList.add(tempTextbox)
        activeSpriteList.add(tempTextbox)
        allSpriteList.add(tempTextbox)

    ########
    # wait for next game
    doneBox = textBox(renderScreen.get_width() / 2, 900, "Next game")
    activeSpriteList.add(doneBox)
    buttonList.add(doneBox)
    allSpriteList.add(doneBox)

    done = False
    while not done:
        events = pygame.event.get()

        checkExit(events)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                for sprite in buttonList:
                    if sprite.rect.collidepoint(mouseTransform(pygame.mouse.get_pos())):
                        if sprite == doneBox:
                            done = True

        allSpriteList.update(events)

        draw(allSpriteList)
    #
    ##################################

    for sprite in activeSpriteList:
        sprite.kill()


def findLongestWord(letterList, dictionary, outputQueue):
    print("starting longest word calculation")
    startTime = time.time()
    dictionaryByLetter = [{}, {}, {}, {}, {}, {}, {}, {}, {}]  # list of dictionaries sorted by number of letters

    for word in dictionary:
        if len(word) <= 9:
            dictionaryByLetter[len(word) - 1][word] = 1  # add word to dictionaries with value 1

    possibleWords = {}
    for i in range(9):
        words = itertools.permutations(letterList, i + 1)  # all permutations of the letters (362880 combinations)

        for word in words:  # check if it is in the dictionary
            tempWord = ''.join(word).lower()
            if tempWord in dictionaryByLetter[i]:
                possibleWords[tempWord] = len(tempWord)

    print("Found all possible words")
    if len(possibleWords) > 0:
        maxLength = len(max(possibleWords, key=possibleWords.get))  # extract all of the longest words
        output = [k for k, v in possibleWords.items() if v == maxLength]
        print(output)
        outputQueue.put(output)
    else:
        print("No words found")
        outputQueue.put([])

    print("Longest word found in: " + str(time.time() - startTime) + " seconds")  # timing


def playLettersGame():
    print("Starting letters game")

    ##################################
    # create lists of consonants and vowels
    vowelsRemaining = []
    vowels =         ["A", "E", "I", "O", "U"]
    vowelFrequency = [15,  21,  13,  13,  5]
    for vowel in vowels:
        for j in range(vowelFrequency[vowels.index(vowel)]):
            vowelsRemaining.append(vowel)

    consonantsRemaining = []
    consonants =        ["B", "C", "D", "F", "G", "H", "J", "K", "L", "M", "N", "P", "Q", "R", "S", "T", "V", "W", "X", "Y", "Z"]  # each consonant, frequency stored below
    consonantFrequency = [2,   3,   6,   2,   3,   2,   1,   1,   5,   4,   8,   4,   1,   9,   9,   9,   1,   1,   1,   1,   1]  # frequency of each consonant in order
    for consonant in consonants:
        for j in range(consonantFrequency[consonants.index(consonant)]):
            consonantsRemaining.append(consonant)
    #
    ##################################

    consonantButton = textBox(renderScreen.get_width() / 2 - 200, 300, "Consonant", dynamicSize=True)
    buttonList.add(consonantButton)
    activeSpriteList.add(consonantButton)
    allSpriteList.add(consonantButton)

    vowelButton = textBox(renderScreen.get_width() / 2 + 200, 300, "Vowel", dynamicSize=True)
    buttonList.add(vowelButton)
    activeSpriteList.add(vowelButton)
    allSpriteList.add(vowelButton)

    selectedLetters = 0
    letterList = []  # list of available letters

    while selectedLetters < 9:  # until 9 letters selected
        events = pygame.event.get()
        checkExit(events)
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                for sprite in buttonList:
                    if sprite.rect.collidepoint(mouseTransform(pygame.mouse.get_pos())):  # has the mouse collided with sprite
                        if sprite == consonantButton:  # add a consonant
                            selectedLetters += 1
                            randNo = random.randint(0, len(consonantsRemaining) - 1)
                            letterList.append(consonantsRemaining[randNo])
                            currentTile = textBox(renderScreen.get_width() / 2 - 375 + 75 * selectedLetters, 400, consonantsRemaining.pop(randNo), size_x=60, size_y=60)
                            tileList.add(currentTile)
                            activeSpriteList.add(currentTile)
                            allSpriteList.add(currentTile)

                        elif sprite == vowelButton:  # add a consonant
                            selectedLetters += 1
                            randNo = random.randint(0, len(vowelsRemaining) - 1)
                            letterList.append(vowelsRemaining[randNo])
                            currentTile = textBox(renderScreen.get_width() / 2 - 375 + 75 * selectedLetters, 400, vowelsRemaining.pop(randNo), size_x=60, size_y=60)
                            tileList.add(currentTile)
                            activeSpriteList.add(currentTile)
                            allSpriteList.add(currentTile)

        allSpriteList.update(events)

        draw(allSpriteList)

    for sprite in buttonList:
        sprite.kill()

    file = open("dictionary.txt")
    englishDictionary = file.readlines()

    for i in range(len(englishDictionary)):
        englishDictionary[i] = englishDictionary[i].rstrip()

    returnQueue = queue.Queue()  # queue to pass the data back to main thread

    workerThread = threading.Thread(target=findLongestWord, args=(letterList, englishDictionary, returnQueue))  # Start second thread
    workerThread.daemon = True  # allow second thread to be stopped
    workerThread.start()  # start the thread

    ##################################
    # Play the game
    countdownClock = timer(renderScreen.get_width() / 2, 800, 1500, 50)
    activeSpriteList.add(countdownClock)
    allSpriteList.add(countdownClock)

    if game.nPlayers == 2:
        while countdownClock.counter >= 0:  # while waiting for timer
            events = pygame.event.get()
            checkExit(events)

            allSpriteList.update(events)

            draw(allSpriteList)

        countdownClock.running = False

        # player 1
        userInput = inputBox(renderScreen.get_width() / 2, 600, size_x=240, defaultText="How long is your word player 1?", validInput=string.digits, dynamicSize=True, maxChars=1)
        activeSpriteList.add(userInput)
        allSpriteList.add(userInput)

        done = False
        while not done:  # while waiting for enter
            events = pygame.event.get()
            checkExit(events)

            for event in events:
                if event.type == pygame.KEYDOWN and (event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER) and len(userInput.text) > 0:
                    done = True
                    break

            allSpriteList.update(events)

            draw(allSpriteList)

        game.player1Target = int(userInput.text)
        userInput.kill()

        # player 2
        userInput = inputBox(renderScreen.get_width() / 2, 600, size_x=240, defaultText="How long is your word player 2?", validInput=string.digits, dynamicSize=True, maxChars=1)
        activeSpriteList.add(userInput)
        allSpriteList.add(userInput)

        done = False
        while not done:  # while waiting for enter
            events = pygame.event.get()
            checkExit(events)

            for event in events:
                if event.type == pygame.KEYDOWN and (event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER) and len(userInput.text) > 0:
                    done = True
                    break

            allSpriteList.update(events)

            draw(allSpriteList)

        game.player2Target = int(userInput.text)
        userInput.kill()

        # player 1
        userInput = inputBox(renderScreen.get_width() / 2, 600, size_x=240, defaultText="What is your " + str(game.player1Target) + " letter word player 1?", validInput=string.ascii_lowercase, dynamicSize=True, maxChars=9)
        activeSpriteList.add(userInput)
        allSpriteList.add(userInput)

        done = False
        while not done:  # while wait for user to enter solution
            events = pygame.event.get()
            checkExit(events)

            allSpriteList.update(events)

            draw(allSpriteList)

            validWordP1 = True

            for event in events:
                if event.type == pygame.KEYDOWN and (event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER) and len(userInput.text) > 0:
                    done = True
                    feedback = textBox(300, 500, "", size_x=300)
                    activeSpriteList.add(feedback)
                    allSpriteList.add(feedback)

                    player1Delta = 0

                    if len(userInput.text) == game.player1Target:  # check same as their target
                        feedbackText = "Your word is worth " + str(len(userInput.text)) + " points"
                        countdownClock.running = False

                        if not userInput.text.lower() in englishDictionary:  # check it is in the dictionary
                            feedbackText = "Word not found"
                            validWordP1 = False
                        else:  # check no letter used twice
                            lettersAvailable = letterList.copy()
                            for letter in userInput.text.lower():
                                if letter.upper() in lettersAvailable:
                                    lettersAvailable.pop(lettersAvailable.index(letter.upper()))
                                else:
                                    feedbackText = "Too many letters used: " + letter.upper() + " not found"
                                    validWordP1 = False

                        feedback.text = feedbackText
                        if validWordP1:  # score the player
                            if len(userInput.text) == 9:
                                player1Delta = 18
                            else:
                                player1Delta = len(userInput.text)
                    else:
                        feedback.text = "Wrong length word"
                        validWordP1 = False
                    break

        game.player1Solution = userInput.text

        # persistent display of solution
        player1Answer = textBox(renderScreen.get_width() / 2, 500, game.player1Solution, size_x=240, dynamicSize=True)
        activeSpriteList.add(player1Answer)
        allSpriteList.add(player1Answer)

        userInput.kill()

        ##########
        # player 2
        feedback2 = textBox(300, 600, "", size_x=300)
        activeSpriteList.add(feedback2)
        allSpriteList.add(feedback2)

        userInput = inputBox(renderScreen.get_width() / 2, 600, size_x=240, defaultText="What is your " + str(game.player2Target) + " letter word player 2?", validInput=string.ascii_lowercase, dynamicSize=True, maxChars=9)
        activeSpriteList.add(userInput)
        allSpriteList.add(userInput)

        done = False
        validWordP2 = True

        while not done:  # while waiting for enter
            events = pygame.event.get()
            checkExit(events)

            for event in events:
                if event.type == pygame.KEYDOWN and (event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER) and len(userInput.text) > 0:
                    done = True
                    player2Delta = 0
                    if len(userInput.text) == game.player2Target:

                        feedbackText = "Your word is worth " + str(len(userInput.text)) + " points"
                        countdownClock.running = False

                        if not userInput.text.lower() in englishDictionary:
                            feedbackText = "Word not found"
                            validWordP2 = False
                        else:
                            lettersAvailable = letterList.copy()
                            for letter in userInput.text.lower():
                                if letter.upper() in lettersAvailable:
                                    lettersAvailable.pop(lettersAvailable.index(letter.upper()))
                                else:
                                    feedbackText = "Too many letters used: " + letter.upper() + " not found"
                                    validWordP2 = False

                        feedback2.text = feedbackText
                        if validWordP2:
                            if len(userInput.text) == 9:
                                player2Delta = 18
                            else:
                                player2Delta = len(userInput.text)
                    else:
                        feedback2.text = "Wrong length word"
                        validWordP2 = False
                    break

            allSpriteList.update(events)

            draw(allSpriteList)

        game.player2Solution = userInput.text

        player2Answer = textBox(renderScreen.get_width() / 2, 600, game.player2Solution, size_x=240, dynamicSize=True)
        activeSpriteList.add(player2Answer)
        allSpriteList.add(player2Answer)

        userInput.kill()

        if player1Delta == player2Delta:  # only highest scorer
            game.player1Score += player1Delta
            game.player2Score += player2Delta
        elif player1Delta > player2Delta:
            game.player1Score += player1Delta
        elif player2Delta > player1Delta:
            game.player2Score += player2Delta

    else:
        feedback = textBox(300, 600, "", size_x=300)
        activeSpriteList.add(feedback)
        allSpriteList.add(feedback)

        userInput = inputBox(renderScreen.get_width() / 2, 600, size_x=240, defaultText="What is the longest word?", validInput=string.ascii_letters, dynamicSize=True, maxChars=9)
        activeSpriteList.add(userInput)
        allSpriteList.add(userInput)

        done = False
        validWordP1 = True
        while not done:
            events = pygame.event.get()

            if countdownClock.counter <= 0 and countdownClock.running:
                feedbackText = "Your word is worth " + str(len(userInput.text)) + " points"
                game.player1Solution = userInput.text
                done = True
                countdownClock.running = False

                if not userInput.text.lower() in englishDictionary:
                    feedbackText = "Word not found"
                    validWordP1 = False
                else:
                    lettersAvailable = letterList.copy()
                    for letter in userInput.text.lower():
                        if letter.upper() in lettersAvailable:
                            lettersAvailable.pop(lettersAvailable.index(letter.upper()))
                        else:
                            feedbackText = "Too many letters used: " + letter.upper() + " not found"
                            validWordP1 = False

                feedback.text = feedbackText

            checkExit(events)

            allSpriteList.update(events)

            draw(allSpriteList)

        if validWordP1:
            if len(userInput.text) == 9:
                game.player1Score += 18
            else:
                game.player1Score += len(userInput.text)

    userInput.selectable = False

    # give feedback
    while workerThread.isAlive():  # wait for solutions to be found
        events = pygame.event.get()

        checkExit(events)

        allSpriteList.update(events)

        draw(allSpriteList)

    longWords = returnQueue.get()  # get the longest words
    feedbackList = pygame.sprite.Group()

    if game.player1Solution in longWords and validWordP1:
        feedback.text = "You found the longest word"

    if game.nPlayers == 2 and game.player2Solution in longWords and validWordP2:
        feedback2.text = "You found the longest word"

    if len(longWords) == 0:
        longWords = ["No valid words found"]

    titleTextbox = textBox(1588, 125, "Longest words found", size_x=425, dynamicSize=True)
    feedbackList.add(titleTextbox)
    activeSpriteList.add(titleTextbox)
    allSpriteList.add(titleTextbox)

    for i in range(min(len(longWords), 10)):  # print up to 10 words
        tempTextbox = textBox(1250 + (225 * ((i % 2) + 1)), 200 + 75 * (math.floor(i / 2)), longWords[i])
        feedbackList.add(tempTextbox)
        activeSpriteList.add(tempTextbox)
        allSpriteList.add(tempTextbox)

    doneBox = textBox(renderScreen.get_width() / 2, 900, "Next game")
    activeSpriteList.add(doneBox)
    buttonList.add(doneBox)
    allSpriteList.add(doneBox)

    done = False
    while not done:
        events = pygame.event.get()

        checkExit(events)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                for sprite in buttonList:
                    if sprite.rect.collidepoint(mouseTransform(pygame.mouse.get_pos())):
                        if sprite == doneBox:
                            done = True

        allSpriteList.update(events)

        draw(allSpriteList)
    #
    ##################################

    for sprite in activeSpriteList:
        sprite.kill()


def playFullGame():
    # Initialise scores and scoreboards
    scoreBox1 = textBox(75, 75, "", 60, 60, dynamicSize=True)
    allSpriteList.add(scoreBox1)

    game.scoreBoard1 = scoreBox1
    game.player1Score = 0

    if game.nPlayers == 2:
        scoreBox2 = textBox(renderScreen.get_width() - 75, 75, "", 60, 60, dynamicSize=True)
        allSpriteList.add(scoreBox2)

        game.scoreBoard2 = scoreBox2
        game.player2Score = 0

    for _ in range(2):
        for _ in range(2):
            playLettersGame()
            print("score: " + str(game.player1Score), str(game.player2Score))

        playNumbersGame()
        print("score: " + str(game.player1Score), str(game.player2Score))

    # display scores
    if game.nPlayers == 1:
        scoreBox1.text = "You scored " + str(game.player1Score)
        scoreBox1.posCenter = [renderScreen.get_width() / 2, renderScreen.get_height() / 2]
    else:
        scoreBox1.text = "P1 scored " + str(game.player1Score)
        scoreBox1.posCenter = [renderScreen.get_width() / 2 - 80, renderScreen.get_height() / 2]
        scoreBox2.text = "P2 scored " + str(game.player2Score)
        scoreBox2.posCenter = [renderScreen.get_width() / 2 + 80, renderScreen.get_height() / 2]

    doneBox = textBox(renderScreen.get_width() / 2, 9 * renderScreen.get_height() / 10, "Next game")
    activeSpriteList.add(doneBox)
    buttonList.add(doneBox)
    allSpriteList.add(doneBox)

    done = False
    while not done:
        events = pygame.event.get()

        checkExit(events)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                for sprite in buttonList:
                    if sprite.rect.collidepoint(mouseTransform(pygame.mouse.get_pos())):
                        if sprite == doneBox:
                            done = True

        allSpriteList.update(events)

        draw(allSpriteList)
    #
    ##################################

    for sprite in allSpriteList:
        sprite.kill()


if __name__ == '__main__':
    #################################
    # Call this function so the Pygame library can initialize itself
    pygame.init()

    # init font
    # this is needed to render fonts on the screen (e.g., to show the score)
    pygame.font.init()
    myFont = pygame.font.SysFont("Helvetica", 24)

    # init a clock
    # need to keep a constant FPS (frames per second)
    clock = pygame.time.Clock()

    # Create an 800x600 sized screen
    Screen = pygame.display.set_mode([0, 0], pygame.FULLSCREEN)
    renderScreen = pygame.Surface([1920, 1080])

    # Set the title of the window
    pygame.display.set_caption('Countdown')

    allSpriteList = pygame.sprite.Group()  # all sprites
    activeSpriteList = pygame.sprite.Group()  # sprites relevant to current page
    tileList = pygame.sprite.Group()  # sprites for numbers or letters
    buttonList = pygame.sprite.Group()  # buttons

    game = gameManager()

    done = False
    while not done:  # repeat playing the game
        checkExit(pygame.event.get())

        # game mode selection
        game.gameType = selectGameMode()

        if game.gameType == "Number":
            playNumbersGame()
        elif game.gameType == "Letter":
            playLettersGame()
        elif game.gameType == "All":
            playFullGame()

    pygame.quit()
