from django.contrib import admin
from .models import Institution, Programme, ProgrammeOffering, ProgrammeRequirement, ClusterGroup, SubClusterGroup, CutOffPoint, ProgrammeLevel

class ProgrammeRequirementInline(admin.TabularInline):
    model = ProgrammeRequirement
    extra = 1

class ProgrammeOfferingInline(admin.TabularInline):
    model = ProgrammeOffering
    extra = 1

class CutOffPointInline(admin.TabularInline):
    model = CutOffPoint
    extra = 1

@admin.register(ProgrammeLevel)
class ProgrammeLevelAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'institution_type', 'location')
    search_fields = ('name', 'code')
    list_filter = ('institution_type',)

@admin.register(ClusterGroup)
class ClusterGroupAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'level', 'subject_1', 'subject_2', 'subject_3', 'subject_4')
    search_fields = ('code', 'name')
    list_filter = ('level',)

@admin.register(SubClusterGroup)
class SubClusterGroupAdmin(admin.ModelAdmin):
    list_display = ('code', 'cluster', 'subject_1', 'subject_2', 'subject_3', 'subject_4')
    search_fields = ('code',)
    list_filter = ('cluster',)

@admin.register(Programme)
class ProgrammeAdmin(admin.ModelAdmin):
    list_display = ('kuccps_code', 'name', 'level', 'cluster', 'sub_cluster', 'job_market_demand', 'minimum_mean_grade')
    list_filter = ('level', 'cluster', 'job_market_demand')
    search_fields = ('name', 'kuccps_code')
    inlines = [ProgrammeRequirementInline, ProgrammeOfferingInline]

@admin.register(ProgrammeOffering)
class ProgrammeOfferingAdmin(admin.ModelAdmin):
    list_display = ('programme', 'institution')
    list_filter = ('institution',)
    search_fields = ('programme__name', 'institution__name')
    inlines = [CutOffPointInline]

@admin.register(ProgrammeRequirement)
class ProgrammeRequirementAdmin(admin.ModelAdmin):
    list_display = ('programme', 'subject', 'subject_category', 'minimum_grade', 'is_category', 'description')
    list_filter = ('minimum_grade', 'is_category')

@admin.register(CutOffPoint)
class CutOffPointAdmin(admin.ModelAdmin):
    list_display = ('offering', 'year', 'cutoff_type', 'weighted_cluster_points', 'mean_grade_cutoff', 'capacity', 'placed_students')
    list_filter = ('year', 'cutoff_type')