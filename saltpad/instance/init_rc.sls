{{'{%'}} set {{project_name}} = salt['pillar.get']('salt_parameters') {{'%}'}}

{{service_name}}_install_path:
  file.directory:
    - name: {{'{{'}}{{project_name}}.install_path{{'}}'}}
    - user: {{'{{'}}{{project_name}}.user{{'}}'}}
    - group: {{'{{'}}{{project_name}}.group{{'}}'}}
    - mode: 755
    - makedirs: true

{{service_name}}_pkg_available_path:
  file.directory:
    - name: {{'{{'}}{{project_name}}.install_path{{'}}'}}/pkg_available
    - user: {{'{{'}}{{project_name}}.user{{'}}'}}
    - group: {{'{{'}}{{project_name}}.group{{'}}'}}
    - mode: 755
    - makedirs: true
    - require:
      - file: {{service_name}}_install_path

{{service_name}}_pkg_installed_path:
  file.directory:
    - name: {{'{{'}}{{project_name}}.install_path{{'}}'}}/pkg_installed
    - user: {{'{{'}}{{project_name}}.user{{'}}'}}
    - group: {{'{{'}}{{project_name}}.group{{'}}'}}
    - mode: 755
    - makedirs: true
    - require:
      - file: {{service_name}}_install_path

{{service_name}}_pkg:
  file.managed:
    - name: {{'{{'}}{{project_name}}.install_path{{'}}'}}/pkg_available/{{service_name}}-{{'{{'}}{{project_name}}.{{service_name}}{{'}}'}}.tar.gz
    - source:  http://{{'{{'}}{{project_name}}.repo_addr{{'}}'}}/{{project_name|upper}}/{{service_name}}-{{'{{'}}{{project_name}}.{{service_name}}{{'}}'}}.tar.gz
    - source_hash: http://{{'{{'}}{{project_name}}.repo_addr{{'}}'}}/{{project_name|upper}}/sha512/{{service_name}}-{{'{{'}}{{project_name}}.{{service_name}}{{'}}'}}.sha512
    - user: {{'{{'}}{{project_name}}.user{{'}}'}}
    - group: {{'{{'}}{{project_name}}.group{{'}}'}}

{{service_name}}_pkg_link:
  file.symlink:
    - name: {{'{{'}}{{project_name}}.install_path{{'}}'}}/pkg_installed/{{service_name}}
    - target: {{'{{'}}{{project_name}}.install_path{{'}}'}}/pkg_available/{{service_name}}-{{'{{'}}{{project_name}}.{{service_name}}{{'}}'}}.tar.gz
    - force: True
    - user: {{'{{'}}{{project_name}}.user{{'}}'}}
    - group: {{'{{'}}{{project_name}}.group{{'}}'}}
    - require:
      - file: {{service_name}}_pkg

{{service_name}}_pkg_install:
  cmd.wait:
    - name: tar zxvf {{service_name}} -C {{'{{'}}{{project_name}}.install_path{{'}}'}}
    - cwd: {{'{{'}}{{project_name}}.install_path{{'}}'}}/pkg_installed
    - user: {{'{{'}}{{project_name}}.user{{'}}'}}
    - group: {{'{{'}}{{project_name}}.group{{'}}'}}
    - watch:
      - file: {{service_name}}_pkg_link

{{'{{'}}{{project_name}}.install_path{{'}}'}}/{{service_name}}:
  file.recurse:
    - source: salt://files/config/{{service_name}}-{{'{{'}}{{project_name}}.{{service_name}}{{'}}'}}-config
    - template: jinja
    - user: {{'{{'}}{{project_name}}.user{{'}}'}}
    - group: {{'{{'}}{{project_name}}.group{{'}}'}}
    - file_mode:  544
    - defaults:    
    {{'{%'}} for key, value in {{project_name}}.iteritems() {{'%}'}}
{%- raw %}
      {{key}}: {{value}}
    {% endfor %}
{%- endraw %}

/etc/init.d/{{project_name}}_{{service_name}}:
  file.symlink:
    - target: {{'{{'}}{{project_name}}.install_path{{'}}'}}/{{service_name}}/{{project_name}}_{{service_name}}
    - force: True
    - user: {{'{{'}}{{project_name}}.user{{'}}'}}
    - group: {{'{{'}}{{project_name}}.group{{'}}'}}
    - watch:
      - cmd: {{service_name}}_pkg_install

{{service_name}}_run:
   service.running:
     - name: {{project_name}}_{{service_name}}
     - sig:  ./{{service_sig}}
     - watch:
        - cmd: {{service_name}}_pkg_install
        - file: {{'{{'}}{{project_name}}.install_path{{'}}'}}/{{service_name}}
        - file: /etc/init.d/{{project_name}}_{{service_name}}


