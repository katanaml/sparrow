const isSidebarExpanded = toggleSidebarEl => {
    return toggleSidebarEl.getAttribute('aria-expanded') === 'true' ? true : false;
}

const toggleSidebar = (sidebarEl, expand, setExpanded = false) => {
    const bottomMenuEl = document.querySelector('[sidebar-bottom-menu]');
    const mainContentEl = document.getElementById('main-content');
    if (expand) {
        sidebarEl.classList.add('lg:w-64');
        sidebarEl.classList.remove('lg:w-16');
        mainContentEl.classList.add('lg:ml-64');
        mainContentEl.classList.remove('lg:ml-16');

        document.querySelectorAll('#' + sidebarEl.getAttribute('id') + ' [sidebar-toggle-item]').forEach(sidebarToggleEl => {
            sidebarToggleEl.classList.remove('lg:hidden');
            sidebarToggleEl.classList.remove('lg:absolute');
        });

        // toggle multi level menu item initial and full text
        document.querySelectorAll('#' + sidebar.getAttribute('id') + ' ul > li > ul > li > a').forEach(e => {
            e.classList.add('pl-11');
            e.classList.remove('px-4');
            e.childNodes[0].classList.remove('hidden');
            e.childNodes[1].classList.add('hidden');
        });

        bottomMenuEl.classList.remove('flex-col', 'space-y-4', 'p-2');
        bottomMenuEl.classList.add('space-x-4', 'p-4');
        setExpanded ? toggleSidebarEl.setAttribute('aria-expanded', 'true') : null;
    } else {
        sidebarEl.classList.remove('lg:w-64');
        sidebarEl.classList.add('lg:w-16');
        mainContentEl.classList.remove('lg:ml-64');
        mainContentEl.classList.add('lg:ml-16');
        document.querySelectorAll('#' + sidebarEl.getAttribute('id') + ' [sidebar-toggle-item]').forEach(sidebarToggleEl => {
            sidebarToggleEl.classList.add('lg:hidden');
            sidebarToggleEl.classList.add('lg:absolute');
        });

        // toggle multi level menu item initial and full text
        document.querySelectorAll('#' + sidebar.getAttribute('id') + ' ul > li > ul > li > a').forEach(e => {
            e.classList.remove('pl-11');
            e.classList.add('px-4');
            e.childNodes[0].classList.add('hidden');
            e.childNodes[1].classList.remove('hidden');
        });

        bottomMenuEl.classList.add('flex-col', 'space-y-4', 'p-2');
        bottomMenuEl.classList.remove('space-x-4', 'p-4');
        setExpanded ? toggleSidebarEl.setAttribute('aria-expanded', 'false') : null;
    }
}

const toggleSidebarEl = document.getElementById('toggleSidebar');
const sidebar = document.getElementById('sidebar');

document.querySelectorAll('#' + sidebar.getAttribute('id') + ' ul > li > ul > li > a').forEach(e => {
    var fullText = e.textContent;
    var firstLetter = fullText.substring(0, 1);

    var fullTextEl = document.createElement('span');
    var firstLetterEl = document.createElement('span');
    firstLetterEl.classList.add('hidden');
    fullTextEl.textContent = fullText;
    firstLetterEl.textContent = firstLetter;

    e.textContent = '';
    e.appendChild(fullTextEl);
    e.appendChild(firstLetterEl);
});

// initialize sidebar
if (localStorage.getItem('sidebarExpanded') !== null) {
    if (localStorage.getItem('sidebarExpanded') === 'true') {
        toggleSidebar(sidebar, true, false);
    } else {
        toggleSidebar(sidebar, false, true);
    }
}

toggleSidebarEl.addEventListener('click', () => {
    localStorage.setItem('sidebarExpanded', !isSidebarExpanded(toggleSidebarEl));
    toggleSidebar(sidebar, !isSidebarExpanded(toggleSidebarEl), true);
});

sidebar.addEventListener('mouseenter', () => {
    if (!isSidebarExpanded(toggleSidebarEl)) {
        toggleSidebar(sidebar, true);
    }
});

sidebar.addEventListener('mouseleave', () => {
    if (!isSidebarExpanded(toggleSidebarEl)) {
        toggleSidebar(sidebar, false);
    }
});

const toggleSidebarMobile = (sidebar, sidebarBackdrop, toggleSidebarMobileHamburger, toggleSidebarMobileClose) => {
    sidebar.classList.toggle('hidden');
    sidebarBackdrop.classList.toggle('hidden');
    toggleSidebarMobileHamburger.classList.toggle('hidden');
    toggleSidebarMobileClose.classList.toggle('hidden');
}

const toggleSidebarMobileEl = document.getElementById('toggleSidebarMobile');
const sidebarBackdrop = document.getElementById('sidebarBackdrop');
const toggleSidebarMobileHamburger = document.getElementById('toggleSidebarMobileHamburger');
const toggleSidebarMobileClose = document.getElementById('toggleSidebarMobileClose');

toggleSidebarMobileEl.addEventListener('click', () => {
    toggleSidebarMobile(sidebar, sidebarBackdrop, toggleSidebarMobileHamburger, toggleSidebarMobileClose);
});

sidebarBackdrop.addEventListener('click', () => {
    toggleSidebarMobile(sidebar, sidebarBackdrop, toggleSidebarMobileHamburger, toggleSidebarMobileClose);
});