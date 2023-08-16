var elements = document.querySelectorAll('.readonly')

for (const element of elements) {
    if (element.querySelector('a')) continue

    element.classList.add('tooltip')

    var tooltiptext = document.createElement('span')
    tooltiptext.classList.add('tooltiptext')
    tooltiptext.innerHTML = 'Copy to Clipboard'

    element.appendChild(tooltiptext)
}

elements = document.querySelectorAll('.tooltip')
for (const element of elements) {
    element.addEventListener('click', () => {
        var child = element.firstChild
        navigator.clipboard.writeText(child.textContent)

        var tooltiptext = element.querySelector('.tooltiptext')
        tooltiptext.innerHTML = 'Copied!'

        setTimeout(() => { tooltiptext.innerHTML = 'Copy to Clipboard' }, 3_000)
    })
}