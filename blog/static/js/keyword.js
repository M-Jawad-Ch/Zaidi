var element = document.querySelectorAll('textarea')[1]
var parent = element.parentElement.parentElement.parentElement.parentElement
var child = document.createElement('div')

child.classList.add('form-row')
child.innerHTML = `<div class="flex-container">
            <label class="required">Keyword</label> 
            <input id="percent" class="vTextField" />
        </div>`

parent.insertBefore(child, element.parentElement.parentElement.parentElement.nextSibling)

input = child.querySelector('input')

input.addEventListener('keypress', e => {
    var key = e.charCode || e.keyCode || 0;
    if (key == 13) {
        e.preventDefault();

        let input = document.querySelector("#percent")
        let words = element.value
        let temp = document.createElement("div")
        temp.innerHTML = words
        words = temp.innerText.toLowerCase()

        let text = input.value.toLowerCase()

        let matches = words.matchAll(text)
        let count = 0

        for (const match of matches) {
            count += 1
        }

        let value = (text.length * count) / words.length * 100

        child.querySelector('label').innerText = `Keyword ${value.toPrecision(2)}% | ${count} / ${words.split(' ').length}`
    }
})