# -*- coding: utf-8 -*-
from odoo import models


class ProjectCollaborator(models.Model):
    _inherit = "project.collaborator"

    def unlink(self):
        # Share Project removes collaborators directly: the task grants go with them.
        removed = [(collab.project_id, collab.partner_id) for collab in self.sudo()]
        res = super().unlink()
        for project, partner in removed:
            project._ms_portal_forget(partner)
        return res
