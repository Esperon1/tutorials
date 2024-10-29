/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";


const SolutionSearch = publicWidget.Widget.extend({
    selector: '.s_solution_search',
    disabledInEditableMode: true,
    events: {
        'click .tag-filter': '_onTagFilterClick',
    },
    init: function () {
        this._super.apply(this, arguments);
        this.activeFilters = [];
        const Shuffle = window.Shuffle; // Assumes you're using the UMD version of Shuffle (for example, from unpkg.com).
        const element = document.getElementById('shuffle-container');
        const sizer = element.querySelector('.js-shuffle-sizer');
        Shuffle.ALL_ITEMS = 'all';
        Shuffle.FILTER_ATTRIBUTE_KEY = 'tags';
        this.shuffleInstance = new Shuffle(element, {
            itemSelector: '.solution-item',
            sizer: sizer, // could also be a selector: '.js-shuffle-sizer'
            filterMode: 'all'
        });
    },
    _onTagFilterClick: function (ev) {
        ev.preventDefault();
        const $tag = $(ev.currentTarget);
        // get tag data attribute value
        const tag = $tag.data('tag');
        // toggle active class
        $tag.toggleClass('active');
        // add or remove tag from activeFilters
        if ($tag.hasClass('active')) {
            this.activeFilters.push(tag);
        } else {
            this.activeFilters = this.activeFilters.filter(function (item) {
                return item !== tag;
            });
        }
        this.shuffleInstance.filter(this.activeFilters);
    }
});

publicWidget.registry.solution_search = SolutionSearch;

export default SolutionSearch;
