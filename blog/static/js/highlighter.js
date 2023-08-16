var textAreas = document.querySelectorAll('textarea')
var form = document.querySelectorAll('form')[1]

for (const textArea of textAreas) {
    textArea.classList.add('invisible')

    let parent = textArea.parentElement
    let newElement = document.createElement('div')

    newElement.classList.add('textarea')
    newElement.contentEditable = 'true'

    newElement.innerText = textArea.value

    parent.appendChild(newElement)
}

form.addEventListener('submit', (e) => {
    for (const textArea of textAreas) {
        let div = textArea.parentElement.querySelector('div.textarea')
        textArea.value = div.innerText
    }
})

var divs = document.querySelectorAll('div.textarea')

for (const div of divs) {
    let text = div.innerText

    let arr = text.split('.').filter(val => val ? true : false).map(x => x.trim())

    div.innerHTML = ''
    arr.forEach((value, index, arr) => {
        if (arr.indexOf(value) != index) {
            let element = document.createElement('span')
            element.classList.add('highlight')
            element.innerText = value + '. '

            div.appendChild(element)
        }
        else {
            let element = document.createTextNode(value + '. ')
            div.appendChild(element)
        }
    })
}