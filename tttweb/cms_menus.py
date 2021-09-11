from menus.base import Modifier
from menus.menu_pool import menu_pool

from cms.models import Page

class MenuModifier(Modifier):

    post_cut = True

    def modify(self, request, nodes, namespace, root_id, post_cut, breadcrumb):
        return nodes

menu_pool.register_modifier(MenuModifier)

