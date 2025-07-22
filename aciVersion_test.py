import re

class AciVersion():
    """
    ACI Version parser class. Parses the version string and provides methods to compare versions.
    Supported version formats:
    - APIC: `5.2(7f)`, `5.2.7f`, `5.2(7.123a)`, `5.2.7.123a`, `5.2(7.123)`, `5.2.7.123`, `aci-apic-dk9.5.2.7f.iso/bin`
    - Switch: `15.2(7f)`, `15.2.7f`, `15.2(7.123a)`, `15.2.7.123a`, `15.2(7.123)`, `15.2.7.123`, `aci-n9000-dk9.15.2.7f.bin`
    """
    v_regex = r'(?:dk9\.)?[1]?(?P<major1>\d)\.(?P<major2>\d)(?:\.|\()(?P<maint>\d+)(?P<QAdot>\.?)(?P<patch1>(?:[a-z]|\d+))(?P<patch2>[a-z]?)\)?'

    def __init__(self, version):
        self.original = version
        v = re.search(self.v_regex, version)
        if not v:
            raise ValueError("Parsing failure of ACI version `%s`" % version)
        self.version = "{major1}.{major2}({maint}{QAdot}{patch1}{patch2})".format(**v.groupdict())
        self.dot_version = "{major1}.{major2}.{maint}{QAdot}{patch1}{patch2}".format(**v.groupdict())
        self.simple_version = "{major1}.{major2}({maint})".format(**v.groupdict())
        self.major_version = "{major1}.{major2}".format(**v.groupdict())
        self.major1 = v.group("major1")
        self.major2 = v.group("major2")
        self.maint = v.group("maint")
        self.patch1 = v.group("patch1")
        self.patch2 = v.group("patch2")
        self.regex = v

    def __str__(self):
        return self.version

    def older_than(self, version):
        v2 = version if isinstance(version, AciVersion) else AciVersion(version)
        for key in ["major1", "major2", "maint"]:
            if int(self.regex.group(key)) > int(v2.regex.group(key)): return False
            elif int(self.regex.group(key)) < int(v2.regex.group(key)): return True
        # Patch1 can be alphabet or number
        if self.patch1.isalpha() and v2.patch1.isdigit():
            return True  # e.g., 5.2(7f) is older than 5.2(7.123)
        elif self.patch1.isdigit() and v2.patch1.isalpha():
            return False
        elif self.patch1.isalpha() and v2.patch1.isalpha():
            if self.patch1 > v2.patch1: return False
            elif self.patch1 < v2.patch1: return True
        elif self.patch1.isdigit() and v2.patch1.isdigit():
            if int(self.patch1) > int(v2.patch1): return False
            elif int(self.patch1) < int(v2.patch1): return True
            # Patch2 (alphabet) is optional.
            if not self.patch2 and v2.patch2:
                return True  # one without Patch2 is older.
            elif self.patch2 and not v2.patch2:
                return False
            elif self.patch2 and v2.patch2:
                if self.patch2 > v2.patch2: return False
                elif self.patch2 < v2.patch2: return True
        return False

    def newer_than(self, version):
        return not self.older_than(version) and not self.same_as(version)

    def same_as(self, version):
        v2 = version if isinstance(version, AciVersion) else AciVersion(version)
        return self.version == v2.version

if __name__ == "__main__":
    # Example usage
    v1 = AciVersion("6.1(3.248)")
    print(v1.simple_version)